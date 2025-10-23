import asyncio
import logging
from typing import List
from src.models import Event

logger = logging.getLogger(__name__)


class EventQueue:
    
    def __init__(self, maxsize: int = 10000):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self.maxsize = maxsize
        logger.info(f"EventQueue initialized with max size: {maxsize}")
    
    async def enqueue(self, event: Event) -> bool:
        try:
            self.queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            logger.warning(f"Queue full, dropping event: {event.topic}/{event.event_id}")
            return False
    
    async def enqueue_batch(self, events: List[Event]) -> int:
        enqueued = 0
        for event in events:
            if await self.enqueue(event):
                enqueued += 1
        return enqueued
    
    async def dequeue(self) -> Event:
        return await self.queue.get()
    
    def qsize(self) -> int:
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        return self.queue.empty()
    
    def is_full(self) -> bool:
        return self.queue.full()
