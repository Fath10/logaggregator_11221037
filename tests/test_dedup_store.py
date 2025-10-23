import pytest
import pytest_asyncio
import asyncio
import os
from pathlib import Path
from src.dedup_store import DedupStore

@pytest_asyncio.fixture
async def dedup_store():
    db_path = "test_dedup.db"
    store = DedupStore(db_path=db_path)
    await store.initialize()
    yield store
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.mark.asyncio
async def test_initialize():
    db_path = "test_init.db"
    store = DedupStore(db_path=db_path)
    await store.initialize()
    
    assert os.path.exists(db_path)
    
    os.remove(db_path)

@pytest.mark.asyncio
async def test_mark_processed_new_event(dedup_store):
    result = await dedup_store.mark_processed(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test"
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_mark_processed_duplicate(dedup_store):

    await dedup_store.mark_processed(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test"
    )

    result = await dedup_store.mark_processed(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test"
    )
    
    assert result is False

@pytest.mark.asyncio
async def test_is_duplicate_new_event(dedup_store):

    result = await dedup_store.is_duplicate("test.topic", "evt-new")
    assert result is False

@pytest.mark.asyncio
async def test_is_duplicate_existing_event(dedup_store):

    await dedup_store.mark_processed(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test"
    )

    result = await dedup_store.is_duplicate("test.topic", "evt-001")
    assert result is True

@pytest.mark.asyncio
async def test_get_processed_count(dedup_store):

    count = await dedup_store.get_processed_count()
    assert count == 0

    await dedup_store.mark_processed("topic1", "evt-001", "2025-10-23T10:00:00Z", "test")
    await dedup_store.mark_processed("topic1", "evt-002", "2025-10-23T10:01:00Z", "test")
    await dedup_store.mark_processed("topic2", "evt-001", "2025-10-23T10:02:00Z", "test")
    
    count = await dedup_store.get_processed_count()
    assert count == 3

@pytest.mark.asyncio
async def test_get_topics(dedup_store):

    await dedup_store.mark_processed("topic1", "evt-001", "2025-10-23T10:00:00Z", "test")
    await dedup_store.mark_processed("topic2", "evt-001", "2025-10-23T10:01:00Z", "test")
    await dedup_store.mark_processed("topic1", "evt-002", "2025-10-23T10:02:00Z", "test")
    
    topics = await dedup_store.get_topics()
    assert len(topics) == 2
    assert "topic1" in topics
    assert "topic2" in topics

@pytest.mark.asyncio
async def test_get_events_by_topic(dedup_store):

    await dedup_store.mark_processed("topic1", "evt-001", "2025-10-23T10:00:00Z", "source1")
    await dedup_store.mark_processed("topic1", "evt-002", "2025-10-23T10:01:00Z", "source2")
    await dedup_store.mark_processed("topic2", "evt-001", "2025-10-23T10:02:00Z", "source3")
    
    events = await dedup_store.get_events_by_topic("topic1")
    assert len(events) == 2
    
    events_limited = await dedup_store.get_events_by_topic("topic1", limit=1)
    assert len(events_limited) == 1

@pytest.mark.asyncio
async def test_get_count_by_topic(dedup_store):

    await dedup_store.mark_processed("topic1", "evt-001", "2025-10-23T10:00:00Z", "test")
    await dedup_store.mark_processed("topic1", "evt-002", "2025-10-23T10:01:00Z", "test")
    await dedup_store.mark_processed("topic2", "evt-001", "2025-10-23T10:02:00Z", "test")
    
    count1 = await dedup_store.get_count_by_topic("topic1")
    count2 = await dedup_store.get_count_by_topic("topic2")
    
    assert count1 == 2
    assert count2 == 1

@pytest.mark.asyncio
async def test_topic_isolation(dedup_store):

    result1 = await dedup_store.mark_processed("topic1", "evt-001", "2025-10-23T10:00:00Z", "test")
    result2 = await dedup_store.mark_processed("topic2", "evt-001", "2025-10-23T10:00:00Z", "test")
    
    assert result1 is True
    assert result2 is True

    is_dup1 = await dedup_store.is_duplicate("topic1", "evt-001")
    is_dup2 = await dedup_store.is_duplicate("topic2", "evt-001")
    
    assert is_dup1 is True
    assert is_dup2 is True
