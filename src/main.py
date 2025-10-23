import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.models import (
    Event, EventBatch, PublishResponse, 
    EventsResponse, StatsResponse
)
from src.event_queue import EventQueue
from src.dedup_store import DedupStore
from src.consumer import EventConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

queue: EventQueue
dedup_store: DedupStore
consumer: EventConsumer
start_time: datetime
received_count: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue, dedup_store, consumer, start_time, received_count
    
    logger.info("Starting Log Aggregator service...")
    
    start_time = datetime.utcnow()
    received_count = 0
    
    dedup_store = DedupStore(db_path="data/dedup.db")
    await dedup_store.initialize()
    
    queue = EventQueue(maxsize=10000)
    
    consumer = EventConsumer(queue, dedup_store)
    await consumer.start()
    
    logger.info("Log Aggregator service started successfully")
    
    yield
    
    logger.info("Shutting down Log Aggregator service...")
    await consumer.stop()
    logger.info("Log Aggregator service stopped")


app = FastAPI(
    title="Log Aggregator Service",
    description="Pub-Sub log aggregator with idempotent processing and deduplication",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "service": "Log Aggregator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "publish": "POST /publish",
            "events": "GET /events?topic=...",
            "stats": "GET /stats",
            "health": "GET /health"
        }
    }


@app.post("/publish", response_model=PublishResponse)
async def publish_events(event_or_batch: Event | EventBatch):
    global received_count
    
    if isinstance(event_or_batch, Event):
        events = [event_or_batch]
    else:
        events = event_or_batch.events
    
    received = len(events)
    received_count += received
    
    accepted = 0
    duplicates = 0
    
    for event in events:
        is_dup = await dedup_store.is_duplicate(event.topic, event.event_id)
        
        if is_dup:
            duplicates += 1
            logger.info(
                f"Duplicate rejected at publish: "
                f"topic={event.topic}, event_id={event.event_id}"
            )
            continue
        
        enqueued = await queue.enqueue(event)
        if enqueued:
            accepted += 1
        else:
            logger.warning(f"Failed to enqueue event: {event.topic}/{event.event_id}")
    
    logger.info(
        f"Published: received={received}, accepted={accepted}, duplicates={duplicates}"
    )
    
    return PublishResponse(
        received=received,
        accepted=accepted,
        duplicates=duplicates,
        message=f"Received {received} events, accepted {accepted}, rejected {duplicates} duplicates"
    )


@app.get("/events", response_model=EventsResponse)
async def get_events(
    topic: str = Query(..., description="Topic to filter events"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of events to return")
):
    try:
        event_tuples = await dedup_store.get_events_by_topic(topic, limit)
        
        events = []
        for event_id, timestamp, source, processed_at in event_tuples:
            events.append(
                Event(
                    topic=topic,
                    event_id=event_id,
                    timestamp=timestamp,
                    source=source,
                    payload={"processed_at": processed_at}
                )
            )
        
        return EventsResponse(
            topic=topic,
            count=len(events),
            events=events
        )
    
    except Exception as e:
        logger.error(f"Error getting events for topic {topic}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    try:
        uptime = (datetime.utcnow() - start_time).total_seconds()
        uptime_hours = int(uptime // 3600)
        uptime_minutes = int((uptime % 3600) // 60)
        uptime_seconds = int(uptime % 60)
        uptime_human = f"{uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
        
        unique_processed = await dedup_store.get_processed_count()
        topics = await dedup_store.get_topics()
        consumer_stats = consumer.get_stats()
        duplicate_dropped = consumer_stats['duplicates']
        
        return StatsResponse(
            received=received_count,
            unique_processed=unique_processed,
            duplicate_dropped=duplicate_dropped,
            topics=topics,
            uptime_seconds=uptime,
            uptime_human=uptime_human
        )
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "consumer_running": consumer.running,
        "queue_size": queue.qsize(),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
