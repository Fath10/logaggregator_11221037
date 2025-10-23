
import asyncio
import requests
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL", "http://localhost:8080")

def create_event(topic: str, event_id: str, source: str, payload: Dict[str, Any]) -> Dict:

    return {
        "topic": topic,
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "payload": payload
    }

def publish_event(event: Dict) -> bool:

    try:
        response = requests.post(
            f"{AGGREGATOR_URL}/publish",
            json=event,
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Published event: {event['topic']}/{event['event_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        return False

def publish_batch(events: List[Dict]) -> bool:

    try:
        response = requests.post(
            f"{AGGREGATOR_URL}/publish",
            json={"events": events},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"Published batch: received={result['received']}, "
            f"accepted={result['accepted']}, duplicates={result['duplicates']}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to publish batch: {e}")
        return False

def simulate_at_least_once_delivery():

    logger.info("Starting at-least-once delivery simulation...")

    logger.info("Waiting for aggregator to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{AGGREGATOR_URL}/health", timeout=2)
            if response.status_code == 200:
                logger.info("Aggregator is ready!")
                break
        except:
            pass
        time.sleep(1)
    else:
        logger.error("Aggregator not ready after 30 seconds")
        return

    logger.info("\n=== Test 1: Simulating retries (same event sent 3 times) ===")
    event_id_1 = f"evt-{uuid.uuid4()}"
    event_1 = create_event(
        topic="user.login",
        event_id=event_id_1,
        source="auth-service",
        payload={"user_id": "user-123", "ip": "192.168.1.1", "success": True}
    )
    
    for i in range(3):
        publish_event(event_1)
        time.sleep(0.5)

    logger.info("\n=== Test 2: Batch with internal duplicates ===")
    event_id_2 = f"evt-{uuid.uuid4()}"
    event_2 = create_event(
        topic="order.created",
        event_id=event_id_2,
        source="order-service",
        payload={"order_id": "ord-456", "amount": 99.99}
    )
    
    batch = [event_2, event_2, event_2]  # Same event 3 times in batch
    publish_batch(batch)
    time.sleep(0.5)

    logger.info("\n=== Test 3: Mixed batch (new + duplicates) ===")
    events = []
    for i in range(5):
        event = create_event(
            topic="api.request",
            event_id=f"evt-{uuid.uuid4()}",
            source="api-gateway",
            payload={"endpoint": f"/api/v1/resource/{i}", "method": "GET"}
        )
        events.append(event)

    events.append(event_1)  # Duplicate from Test 1
    events.append(event_2)  # Duplicate from Test 2
    
    publish_batch(events)
    time.sleep(0.5)

    logger.info("\n=== Test 4: Multiple topics ===")
    topics = ["user.login", "user.logout", "order.created", "order.shipped", "payment.processed"]
    
    for topic in topics:
        for i in range(3):
            event_id = f"evt-{uuid.uuid4()}"
            event = create_event(
                topic=topic,
                event_id=event_id,
                source="test-publisher",
                payload={"iteration": i, "test": "multiple_topics"}
            )
            publish_event(event)
            time.sleep(0.1)

    logger.info("\n=== Test 5: High-frequency with occasional duplicates ===")
    saved_events = []
    
    for i in range(20):
        event_id = f"evt-{uuid.uuid4()}"
        event = create_event(
            topic="metrics.collected",
            event_id=event_id,
            source="monitoring-service",
            payload={"metric": "cpu_usage", "value": 45 + i, "host": "server-01"}
        )
        
        publish_event(event)

        if i % 5 == 0:
            saved_events.append(event)
        
        time.sleep(0.1)

    logger.info("Resending saved events to simulate duplicates...")
    for event in saved_events:
        publish_event(event)
        time.sleep(0.1)

    time.sleep(2)

    logger.info("\n=== Final Statistics ===")
    try:
        response = requests.get(f"{AGGREGATOR_URL}/stats", timeout=5)
        stats = response.json()
        logger.info(f"Total received: {stats['received']}")
        logger.info(f"Unique processed: {stats['unique_processed']}")
        logger.info(f"Duplicates dropped: {stats['duplicate_dropped']}")
        logger.info(f"Topics: {stats['topics']}")
        logger.info(f"Uptime: {stats['uptime_human']}")
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")

    logger.info("\n=== Query Events by Topic ===")
    for topic in ["user.login", "order.created", "metrics.collected"]:
        try:
            response = requests.get(
                f"{AGGREGATOR_URL}/events",
                params={"topic": topic, "limit": 5},
                timeout=5
            )
            result = response.json()
            logger.info(f"Topic '{topic}': {result['count']} events")
        except Exception as e:
            logger.error(f"Failed to query topic {topic}: {e}")
    
    logger.info("\n=== Simulation Complete ===")

if __name__ == "__main__":
    simulate_at_least_once_delivery()
