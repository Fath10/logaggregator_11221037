
import pytest
from pydantic import ValidationError
from src.models import Event, EventBatch, PublishResponse, EventsResponse, StatsResponse

def test_event_valid():

    event = Event(
        topic="test.topic",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test",
        payload={"key": "value"}
    )
    
    assert event.topic == "test.topic"
    assert event.event_id == "evt-001"
    assert event.payload["key"] == "value"

def test_event_missing_required_field():

    with pytest.raises(ValidationError):
        Event(
            topic="test.topic",
            event_id="evt-001",

            source="test",
            payload={}
        )

def test_event_empty_topic():

    with pytest.raises(ValidationError):
        Event(
            topic="",  # Empty topic
            event_id="evt-001",
            timestamp="2025-10-23T10:00:00Z",
            source="test",
            payload={}
        )

def test_event_invalid_timestamp():

    with pytest.raises(ValidationError):
        Event(
            topic="test",
            event_id="evt-001",
            timestamp="not-a-timestamp",
            source="test",
            payload={}
        )

def test_event_valid_iso8601_formats():

    valid_formats = [
        "2025-10-23T10:00:00Z",
        "2025-10-23T10:00:00+00:00",
        "2025-10-23T10:00:00.123456Z",
        "2025-10-23T10:00:00",
    ]
    
    for ts in valid_formats:
        event = Event(
            topic="test",
            event_id="evt-001",
            timestamp=ts,
            source="test",
            payload={}
        )
        assert event.timestamp == ts

def test_event_empty_payload():

    event = Event(
        topic="test",
        event_id="evt-001",
        timestamp="2025-10-23T10:00:00Z",
        source="test",
        payload={}
    )
    
    assert event.payload == {}

def test_event_batch_valid():

    batch = EventBatch(
        events=[
            Event(
                topic="test",
                event_id="evt-001",
                timestamp="2025-10-23T10:00:00Z",
                source="test",
                payload={}
            ),
            Event(
                topic="test",
                event_id="evt-002",
                timestamp="2025-10-23T10:01:00Z",
                source="test",
                payload={}
            )
        ]
    )
    
    assert len(batch.events) == 2

def test_event_batch_empty():

    with pytest.raises(ValidationError):
        EventBatch(events=[])

def test_publish_response():

    response = PublishResponse(
        received=5,
        accepted=4,
        duplicates=1,
        message="Test message"
    )
    
    assert response.received == 5
    assert response.accepted == 4
    assert response.duplicates == 1

def test_events_response():

    response = EventsResponse(
        topic="test.topic",
        count=1,
        events=[
            Event(
                topic="test.topic",
                event_id="evt-001",
                timestamp="2025-10-23T10:00:00Z",
                source="test",
                payload={}
            )
        ]
    )
    
    assert response.topic == "test.topic"
    assert response.count == 1
    assert len(response.events) == 1

def test_stats_response():

    response = StatsResponse(
        received=100,
        unique_processed=80,
        duplicate_dropped=20,
        topics=["topic1", "topic2"],
        uptime_seconds=3600.5,
        uptime_human="1h 0m 0s"
    )
    
    assert response.received == 100
    assert response.unique_processed == 80
    assert response.duplicate_dropped == 20
    assert len(response.topics) == 2
    assert response.uptime_seconds == 3600.5
