
import pytest
import asyncio
from src.event_queue import EventQueue
from src.models import Event

@pytest.fixture
def event_queue():

    return EventQueue(maxsize=10)

@pytest.fixture
def sample_event():

    return Event(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test",
        payload={"test": True}
    )

@pytest.mark.asyncio
async def test_enqueue_success(event_queue, sample_event):

    result = await event_queue.enqueue(sample_event)
    assert result is True
    assert event_queue.qsize() == 1

@pytest.mark.asyncio
async def test_enqueue_full_queue(sample_event):

    small_queue = EventQueue(maxsize=2)

    await small_queue.enqueue(sample_event)
    await small_queue.enqueue(sample_event)

    result = await small_queue.enqueue(sample_event)
    assert result is False
    assert small_queue.qsize() == 2

@pytest.mark.asyncio
async def test_dequeue(event_queue, sample_event):

    await event_queue.enqueue(sample_event)
    
    dequeued = await event_queue.dequeue()
    assert dequeued.event_id == sample_event.event_id
    assert event_queue.qsize() == 0

@pytest.mark.asyncio
async def test_enqueue_batch(event_queue):

    events = [
        Event(
            topic="test",
            event_id=f"evt-{i}",
            timestamp="2025-10-23T10:00:00Z",
            source="test",
            payload={}
        )
        for i in range(5)
    ]
    
    enqueued = await event_queue.enqueue_batch(events)
    assert enqueued == 5
    assert event_queue.qsize() == 5

@pytest.mark.asyncio
async def test_is_empty(event_queue, sample_event):

    assert event_queue.is_empty() is True
    
    await event_queue.enqueue(sample_event)
    assert event_queue.is_empty() is False

@pytest.mark.asyncio
async def test_is_full():

    small_queue = EventQueue(maxsize=1)
    assert small_queue.is_full() is False
    
    event = Event(
        topic="test",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test",
        payload={}
    )
    await small_queue.enqueue(event)
    assert small_queue.is_full() is True

@pytest.mark.asyncio
async def test_qsize(event_queue):

    assert event_queue.qsize() == 0
    
    events = [
        Event(
            topic="test",
            event_id=f"evt-{i}",
            timestamp="2025-10-23T10:00:00Z",
            source="test",
            payload={}
        )
        for i in range(3)
    ]
    
    await event_queue.enqueue_batch(events)
    assert event_queue.qsize() == 3

@pytest.mark.asyncio
async def test_fifo_order(event_queue):

    events = [
        Event(
            topic="test",
            event_id=f"evt-{i}",
            timestamp="2025-10-23T10:00:00Z",
            source="test",
            payload={"order": i}
        )
        for i in range(3)
    ]

    await event_queue.enqueue_batch(events)

    for i in range(3):
        event = await event_queue.dequeue()
        assert event.event_id == f"evt-{i}"
        assert event.payload["order"] == i
