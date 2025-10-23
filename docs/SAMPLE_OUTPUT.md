# Sample Output & Examples

## 🎬 Sample Log Output

### Service Startup

```
2025-10-23 10:30:00 - src.main - INFO - Starting Log Aggregator service...
2025-10-23 10:30:00 - src.dedup_store - INFO - DedupStore initialized with database: data/dedup.db
2025-10-23 10:30:00 - src.dedup_store - INFO - DedupStore database initialized
2025-10-23 10:30:00 - src.event_queue - INFO - EventQueue initialized with max size: 10000
2025-10-23 10:30:00 - src.consumer - INFO - EventConsumer initialized
2025-10-23 10:30:00 - src.consumer - INFO - EventConsumer started
2025-10-23 10:30:00 - src.consumer - INFO - Consumer loop started
2025-10-23 10:30:00 - src.main - INFO - Log Aggregator service started successfully
2025-10-23 10:30:00 - uvicorn.access - INFO - Application startup complete.
```

### Event Processing (Unique Event)

```
2025-10-23 10:31:15 - src.main - INFO - Published: received=1, accepted=1, duplicates=0
2025-10-23 10:31:15 - src.consumer - INFO - Event processed successfully: topic=user.login, event_id=evt-12345, source=auth-service
```

### Duplicate Detection

```
2025-10-23 10:31:30 - src.main - INFO - Duplicate rejected at publish: topic=user.login, event_id=evt-12345
2025-10-23 10:31:30 - src.main - INFO - Published: received=1, accepted=0, duplicates=1
2025-10-23 10:31:30 - src.consumer - WARNING - Duplicate event detected and dropped: topic=user.login, event_id=evt-12345, source=auth-service
```

### Batch Processing

```
2025-10-23 10:32:00 - src.main - INFO - Published: received=5, accepted=4, duplicates=1
2025-10-23 10:32:00 - src.consumer - INFO - Event processed successfully: topic=order.created, event_id=order-001, source=order-service
2025-10-23 10:32:00 - src.consumer - INFO - Event processed successfully: topic=order.created, event_id=order-002, source=order-service
2025-10-23 10:32:00 - src.consumer - INFO - Event processed successfully: topic=order.created, event_id=order-003, source=order-service
2025-10-23 10:32:00 - src.consumer - WARNING - Duplicate event detected and dropped: topic=order.created, event_id=order-001, source=order-service
2025-10-23 10:32:00 - src.consumer - INFO - Event processed successfully: topic=order.created, event_id=order-004, source=order-service
```

## 📤 Sample API Responses

### POST /publish (Single Event - Success)

**Request:**
```json
{
  "topic": "user.login",
  "event_id": "evt-001",
  "timestamp": "2025-10-23T10:00:00Z",
  "source": "auth-service",
  "payload": {
    "user_id": "user-123",
    "ip_address": "192.168.1.1"
  }
}
```

**Response (200 OK):**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0,
  "message": "Received 1 events, accepted 1, rejected 0 duplicates"
}
```

### POST /publish (Duplicate Event)

**Request:** (Same as above)

**Response (200 OK):**
```json
{
  "received": 1,
  "accepted": 0,
  "duplicates": 1,
  "message": "Received 1 events, accepted 0, rejected 1 duplicates"
}
```

### POST /publish (Batch with Mixed Results)

**Request:**
```json
{
  "events": [
    {
      "topic": "order.created",
      "event_id": "order-001",
      "timestamp": "2025-10-23T10:05:00Z",
      "source": "order-service",
      "payload": {"order_id": "12345", "amount": 99.99}
    },
    {
      "topic": "order.created",
      "event_id": "order-002",
      "timestamp": "2025-10-23T10:06:00Z",
      "source": "order-service",
      "payload": {"order_id": "12346", "amount": 149.99}
    },
    {
      "topic": "order.created",
      "event_id": "order-001",
      "timestamp": "2025-10-23T10:05:00Z",
      "source": "order-service",
      "payload": {"order_id": "12345", "amount": 99.99}
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "received": 3,
  "accepted": 2,
  "duplicates": 1,
  "message": "Received 3 events, accepted 2, rejected 1 duplicates"
}
```

### GET /events?topic=user.login

**Response (200 OK):**
```json
{
  "topic": "user.login",
  "count": 5,
  "events": [
    {
      "topic": "user.login",
      "event_id": "evt-005",
      "timestamp": "2025-10-23T10:30:00Z",
      "source": "auth-service",
      "payload": {
        "processed_at": "2025-10-23T10:30:01.123456"
      }
    },
    {
      "topic": "user.login",
      "event_id": "evt-004",
      "timestamp": "2025-10-23T10:25:00Z",
      "source": "auth-service",
      "payload": {
        "processed_at": "2025-10-23T10:25:01.234567"
      }
    },
    {
      "topic": "user.login",
      "event_id": "evt-003",
      "timestamp": "2025-10-23T10:20:00Z",
      "source": "auth-service",
      "payload": {
        "processed_at": "2025-10-23T10:20:01.345678"
      }
    }
  ]
}
```

### GET /stats

**Response (200 OK):**
```json
{
  "received": 150,
  "unique_processed": 120,
  "duplicate_dropped": 30,
  "topics": [
    "api.request",
    "metrics.collected",
    "order.created",
    "order.shipped",
    "payment.processed",
    "user.login",
    "user.logout"
  ],
  "uptime_seconds": 3665.5,
  "uptime_human": "1h 1m 5s"
}
```

### GET /health

**Response (200 OK):**
```json
{
  "status": "healthy",
  "consumer_running": true,
  "queue_size": 5,
  "timestamp": "2025-10-23T10:30:45.123456"
}
```

### GET / (Root)

**Response (200 OK):**
```json
{
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
```

## 🧪 Test Publisher Output

### Full Test Run

```
2025-10-23 10:35:00 - __main__ - INFO - Starting at-least-once delivery simulation...
2025-10-23 10:35:00 - __main__ - INFO - Waiting for aggregator to be ready...
2025-10-23 10:35:05 - __main__ - INFO - Aggregator is ready!

2025-10-23 10:35:05 - __main__ - INFO - 
=== Test 1: Simulating retries (same event sent 3 times) ===
2025-10-23 10:35:05 - __main__ - INFO - Published event: user.login/evt-abc-123
2025-10-23 10:35:06 - __main__ - INFO - Published event: user.login/evt-abc-123
2025-10-23 10:35:06 - __main__ - INFO - Published event: user.login/evt-abc-123

2025-10-23 10:35:07 - __main__ - INFO - 
=== Test 2: Batch with internal duplicates ===
2025-10-23 10:35:07 - __main__ - INFO - Published batch: received=3, accepted=1, duplicates=2

2025-10-23 10:35:07 - __main__ - INFO - 
=== Test 3: Mixed batch (new + duplicates) ===
2025-10-23 10:35:08 - __main__ - INFO - Published batch: received=7, accepted=5, duplicates=2

2025-10-23 10:35:08 - __main__ - INFO - 
=== Test 4: Multiple topics ===
2025-10-23 10:35:08 - __main__ - INFO - Published event: user.login/evt-001
2025-10-23 10:35:08 - __main__ - INFO - Published event: user.login/evt-002
2025-10-23 10:35:08 - __main__ - INFO - Published event: user.login/evt-003
2025-10-23 10:35:09 - __main__ - INFO - Published event: user.logout/evt-004
...

2025-10-23 10:35:12 - __main__ - INFO - 
=== Test 5: High-frequency with occasional duplicates ===
2025-10-23 10:35:12 - __main__ - INFO - Published event: metrics.collected/evt-metric-001
2025-10-23 10:35:12 - __main__ - INFO - Published event: metrics.collected/evt-metric-002
...
2025-10-23 10:35:14 - __main__ - INFO - Resending saved events to simulate duplicates...

2025-10-23 10:35:16 - __main__ - INFO - 
=== Final Statistics ===
2025-10-23 10:35:16 - __main__ - INFO - Total received: 58
2025-10-23 10:35:16 - __main__ - INFO - Unique processed: 45
2025-10-23 10:35:16 - __main__ - INFO - Duplicates dropped: 13
2025-10-23 10:35:16 - __main__ - INFO - Topics: ['api.request', 'metrics.collected', 'order.created', 'order.shipped', 'payment.processed', 'user.login', 'user.logout']
2025-10-23 10:35:16 - __main__ - INFO - Uptime: 0h 5m 16s

2025-10-23 10:35:16 - __main__ - INFO - 
=== Query Events by Topic ===
2025-10-23 10:35:16 - __main__ - INFO - Topic 'user.login': 3 events
2025-10-23 10:35:16 - __main__ - INFO - Topic 'order.created': 5 events
2025-10-23 10:35:16 - __main__ - INFO - Topic 'metrics.collected': 20 events

2025-10-23 10:35:16 - __main__ - INFO - 
=== Simulation Complete ===
```

## 📊 Validation Scenarios

### Scenario 1: Normal Operation

**Input:**
- Event A (first time) → ✅ Accepted
- Event B (first time) → ✅ Accepted
- Event C (first time) → ✅ Accepted

**Stats:**
- Received: 3
- Unique processed: 3
- Duplicates dropped: 0

### Scenario 2: Duplicate Detection

**Input:**
- Event A (first time) → ✅ Accepted
- Event A (duplicate) → ❌ Rejected
- Event A (duplicate) → ❌ Rejected

**Stats:**
- Received: 3
- Unique processed: 1
- Duplicates dropped: 2

**Logs:**
```
INFO - Event processed successfully: topic=test, event_id=A
WARNING - Duplicate event detected and dropped: topic=test, event_id=A
WARNING - Duplicate event detected and dropped: topic=test, event_id=A
```

### Scenario 3: Crash & Recovery

**Phase 1 (Before Crash):**
- Event A → ✅ Accepted
- Event B → ✅ Accepted

**Container Restart**

**Phase 2 (After Restart):**
- Event A → ❌ Rejected (duplicate)
- Event C → ✅ Accepted (new)

**Verification:**
- Event A still in SQLite ✅
- Deduplication persists ✅

### Scenario 4: Batch Processing

**Input (Batch):**
```json
{
  "events": [
    {"event_id": "A", ...},  // New
    {"event_id": "B", ...},  // New
    {"event_id": "A", ...},  // Duplicate in batch
    {"event_id": "C", ...}   // New
  ]
}
```

**Result:**
- Accepted: 3 (A, B, C)
- Duplicates: 1 (second A)

**Response:**
```json
{
  "received": 4,
  "accepted": 3,
  "duplicates": 1,
  "message": "Received 4 events, accepted 3, rejected 1 duplicates"
}
```

### Scenario 5: Multiple Topics

**Input:**
- Topic "user.login", Event "evt-001" → ✅ Accepted
- Topic "user.logout", Event "evt-001" → ✅ Accepted (different topic!)
- Topic "user.login", Event "evt-001" → ❌ Rejected (duplicate)

**Explanation:**
- Event ID "evt-001" can exist in multiple topics
- Dedup key is `(topic, event_id)` not just `event_id`

## 🎯 Performance Metrics

### Sample Performance Data

```
Service Started: 2025-10-23 10:00:00
Current Time:    2025-10-23 11:30:00
Uptime:          1h 30m 0s (5400 seconds)

Total Events Received:      54,000
Unique Events Processed:    45,000
Duplicates Dropped:          9,000
Deduplication Rate:         16.67%

Average Throughput:         10 events/second
Peak Throughput:            150 events/second
Average Latency (publish):  8ms
Average Latency (process):  12ms

Memory Usage:               52 MB
CPU Usage:                  5%
Disk Usage (SQLite):        45 MB (45,000 events × ~1KB)

Topics Active:              12
Events in Queue:            5
Consumer Status:            Running
Health Status:              Healthy
```

## 🔍 Validation Examples

### Schema Validation (Invalid Event)

**Request:**
```json
{
  "topic": "",
  "event_id": "evt-001",
  "timestamp": "invalid-date",
  "source": "test"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    },
    {
      "loc": ["body", "timestamp"],
      "msg": "timestamp must be in ISO8601 format",
      "type": "value_error"
    }
  ]
}
```

### Missing Required Fields

**Request:**
```json
{
  "topic": "test"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "event_id"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "timestamp"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "source"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 💡 Tips for Reading Logs

### Identifying Duplicates
```bash
# Count duplicates
docker logs log-aggregator | grep "Duplicate event detected" | wc -l

# Show duplicate events
docker logs log-aggregator | grep "Duplicate"
```

### Monitoring Processing
```bash
# Count processed events
docker logs log-aggregator | grep "processed successfully" | wc -l

# Show processing rate
docker logs log-aggregator | grep "processed successfully" | tail -20
```

### Checking for Errors
```bash
# Show errors only
docker logs log-aggregator | grep "ERROR"

# Show warnings
docker logs log-aggregator | grep "WARNING"
```

---

**These examples demonstrate the complete functionality of the Log Aggregator system!** 🎉
