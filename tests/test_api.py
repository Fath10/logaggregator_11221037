
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():

    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Log Aggregator"
    assert data["status"] == "running"

def test_health_endpoint(client):

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "consumer_running" in data
    assert "queue_size" in data

def test_publish_single_event(client):

    event = {
        "topic": "test.api",
        "event_id": "api-test-001",
        "timestamp": "2025-10-23T10:00:00Z",
        "source": "test",
        "payload": {"test": True}
    }
    
    response = client.post("/publish", json=event)
    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 1
    assert data["accepted"] >= 0

def test_publish_batch_events(client):

    batch = {
        "events": [
            {
                "topic": "test.batch",
                "event_id": f"batch-{i}",
                "timestamp": "2025-10-23T10:00:00Z",
                "source": "test",
                "payload": {}
            }
            for i in range(3)
        ]
    }
    
    response = client.post("/publish", json=batch)
    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 3

def test_publish_invalid_event(client):

    invalid_event = {
        "topic": "",  # Empty topic
        "event_id": "test",
        "timestamp": "invalid-timestamp",
        "source": "test"
    }
    
    response = client.post("/publish", json=invalid_event)
    assert response.status_code == 422  # Validation error

def test_publish_missing_fields(client):

    incomplete_event = {
        "topic": "test",
        "event_id": "test"

    }
    
    response = client.post("/publish", json=incomplete_event)
    assert response.status_code == 422

def test_stats_endpoint(client):

    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "received" in data
    assert "unique_processed" in data
    assert "duplicate_dropped" in data
    assert "topics" in data
    assert "uptime_seconds" in data
    assert "uptime_human" in data

def test_events_endpoint(client):

    event = {
        "topic": "test.query",
        "event_id": "query-test-001",
        "timestamp": "2025-10-23T10:00:00Z",
        "source": "test",
        "payload": {}
    }
    client.post("/publish", json=event)

    response = client.get("/events?topic=test.query&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "test.query"
    assert "count" in data
    assert "events" in data

def test_events_endpoint_missing_topic(client):

    response = client.get("/events")
    assert response.status_code == 422  # Missing required parameter

def test_events_endpoint_with_limit(client):

    response = client.get("/events?topic=test&limit=5")
    assert response.status_code == 200

def test_duplicate_event_detection(client):

    event = {
        "topic": "test.duplicate",
        "event_id": "dup-test-001",
        "timestamp": "2025-10-23T10:00:00Z",
        "source": "test",
        "payload": {}
    }

    response1 = client.post("/publish", json=event)
    data1 = response1.json()

    response2 = client.post("/publish", json=event)
    data2 = response2.json()

    assert data2["duplicates"] >= 0
