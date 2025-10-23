import asyncio
import logging
from typing import Dict, Any
from src.event_queue import EventQueue
from src.dedup_store import DedupStore
from src.models import Event

logger = logging.getLogger(__name__)


class EventConsumer:
    
    def __init__(self, queue: EventQueue, dedup_store: DedupStore):
        self.queue = queue
        self.dedup_store = dedup_store
        self.running = False
        self._task = None
        self.stats = {
            'processed': 0,
            'duplicates': 0,
        }
        logger.info("EventConsumer initialized")
    
    async def start(self):
        if self.running:
            logger.warning("Consumer already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("EventConsumer started")
    
    async def stop(self):
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("EventConsumer stopped")
    
    async def _consume_loop(self):
        logger.info("Consumer loop started")
        
        while self.running:
            try:
                try:
                    event = await asyncio.wait_for(self.queue.dequeue(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                await self._process_event(event)
                
            except asyncio.CancelledError:
                logger.info("Consumer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)
        
        logger.info("Consumer loop ended")
    
    async def _process_event(self, event: Event):
        try:
            is_dup = await self.dedup_store.is_duplicate(event.topic, event.event_id)
            
            if is_dup:
                self.stats['duplicates'] += 1
                logger.warning(
                    f"Duplicate event detected and dropped: "
                    f"topic={event.topic}, event_id={event.event_id}, source={event.source}"
                )
                return
            
            marked = await self.dedup_store.mark_processed(
                topic=event.topic,
                event_id=event.event_id,
                timestamp=event.timestamp,
                source=event.source
            )
            
            if not marked:
                self.stats['duplicates'] += 1
                logger.warning(
                    f"Duplicate event detected (race condition): "
                    f"topic={event.topic}, event_id={event.event_id}"
                )
                return
            
            await self._handle_event(event)
            self.stats['processed'] += 1
            
            logger.info(
                f"Event processed successfully: "
                f"topic={event.topic}, event_id={event.event_id}, source={event.source}"
            )
            
        except Exception as e:
            logger.error(
                f"Error processing event {event.topic}/{event.event_id}: {e}",
                exc_info=True
            )
    
    async def _handle_event(self, event: Event):
        await asyncio.sleep(0.01)
        
        logger.debug(f"Handling event: {event.topic}/{event.event_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'processed': self.stats['processed'],
            'duplicates': self.stats['duplicates'],
            'running': self.running,
            'queue_size': self.queue.qsize(),
        }
