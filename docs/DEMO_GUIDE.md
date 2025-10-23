# 🎬 Demo Guide - UTS Log Aggregator

Panduan lengkap untuk demonstrasi sistem Log Aggregator dengan fokus pada:
- Build & Run container
- Idempotency & Deduplication
- Stats monitoring
- Crash tolerance & persistence
- Arsitektur sistem

---

## 📋 Prerequisites

- Docker installed
- curl atau PowerShell
- Port 8080 tersedia

---

## 🚀 Step 1: Build Image dan Menjalankan Container

### 1.1 Build Docker Image

```bash
# Build image dari Dockerfile
docker build -t uts-aggregator .
```

**Output yang diharapkan:**
```
[+] Building 45.2s (14/14) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.23kB
 => [internal] load .dockerignore
 => [stage-1 1/6] FROM docker.io/library/python:3.11-slim
 => [stage-1 6/6] RUN mkdir -p /app/data && chown -R appuser:appuser /app
 => exporting to image
 => => naming to docker.io/library/uts-aggregator
```

**✅ Verification:**
```bash
# Cek image berhasil dibuat
docker images | grep uts-aggregator
```

Expected output:
```
uts-aggregator    latest    abc123def456    2 minutes ago    245MB
```

### 1.2 Run Container

```bash
# Run container dengan port mapping
docker run -d \
  -p 8080:8080 \
  --name log-aggregator \
  -v $(pwd)/data:/app/data \
  uts-aggregator
```

**Parameter Explanation:**
- `-d`: Run in detached mode (background)
- `-p 8080:8080`: Map port 8080 host → container
- `--name log-aggregator`: Nama container untuk referensi mudah
- `-v $(pwd)/data:/app/data`: Mount volume untuk persistence

**PowerShell version:**
```powershell
docker run -d -p 8080:8080 --name log-aggregator -v ${PWD}/data:/app/data uts-aggregator
```

### 1.3 Verify Container Running

```bash
# Check container status
docker ps

# Check logs
docker logs log-aggregator

# Health check
curl http://localhost:8080/health
```

**Expected health output:**
```json
{
  "status": "healthy",
  "consumer_running": true,
  "queue_size": 0
}
```

---

## 🎯 Step 2: Demonstrasi Idempotency & Deduplication

### 2.1 Check Initial State

```bash
# Get current stats (should be empty)
curl http://localhost:8080/stats
```

**Expected output:**
```json
{
  "received": 0,
  "unique_processed": 0,
  "duplicate_dropped": 0,
  "topics": [],
  "uptime_seconds": 10.5,
  "uptime_human": "00:00:10"
}
```

### 2.2 Send First Event (Original)

```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "demo-app",
    "payload": {
      "user_id": 123,
      "username": "alice",
      "ip": "192.168.1.1"
    }
  }'
```

**Expected response:**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0
}
```

**✅ Analysis:** Event diterima dan diproses (accepted = 1)

### 2.3 Check Stats After First Event

```bash
curl http://localhost:8080/stats
```

**Expected output:**
```json
{
  "received": 1,
  "unique_processed": 1,
  "duplicate_dropped": 0,
  "topics": ["user.login"],
  "uptime_seconds": 25.3,
  "uptime_human": "00:00:25"
}
```

**📊 Key Observations:**
- `received`: 1 (event masuk)
- `unique_processed`: 1 (event diproses)
- `duplicate_dropped`: 0 (belum ada duplikat)

### 2.4 Query Events by Topic

```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

**Expected output:**
```json
{
  "topic": "user.login",
  "count": 1,
  "events": [
    {
      "event_id": "evt-demo-001",
      "timestamp": "2025-10-23T10:00:00Z",
      "source": "demo-app",
      "payload": {
        "user_id": 123,
        "username": "alice",
        "ip": "192.168.1.1",
        "processed_at": "2025-10-23T10:00:15.123456"
      }
    }
  ]
}
```

### 2.5 Send DUPLICATE Event (Simulate At-Least-Once)

```bash
# Kirim event PERSIS SAMA (same topic + event_id)
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-demo-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "demo-app",
    "payload": {
      "user_id": 123,
      "username": "alice",
      "ip": "192.168.1.1"
    }
  }'
```

**Expected response:**
```json
{
  "received": 1,
  "accepted": 0,
  "duplicates": 1
}
```

**✅ PROOF OF IDEMPOTENCY:**
- `accepted`: 0 (event ditolak!)
- `duplicates`: 1 (terdeteksi sebagai duplikat!)

### 2.6 Check Stats After Duplicate

```bash
curl http://localhost:8080/stats
```

**Expected output:**
```json
{
  "received": 2,
  "unique_processed": 1,
  "duplicate_dropped": 1,
  "topics": ["user.login"],
  "uptime_seconds": 45.7,
  "uptime_human": "00:00:45"
}
```

**📊 Analysis:**
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| `received` | 1 | 2 | +1 (event masuk) |
| `unique_processed` | 1 | 1 | **TIDAK BERUBAH** ✅ |
| `duplicate_dropped` | 0 | 1 | +1 (duplikat ditolak) ✅ |

**✅ CONCLUSION:** Event dengan `(topic, event_id)` yang sama **hanya diproses sekali** meski dikirim berkali-kali!

### 2.7 Verify Events Count Unchanged

```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

**Expected output:**
```json
{
  "topic": "user.login",
  "count": 1,
  "events": [
    {
      "event_id": "evt-demo-001",
      ...
    }
  ]
}
```

**✅ Count masih 1** (tidak ada duplikasi di database!)

### 2.8 Check Container Logs

```bash
docker logs log-aggregator --tail 20
```

**Expected logs:**
```
INFO - Event queued: topic=user.login, event_id=evt-demo-001
INFO - Processing event: topic=user.login, event_id=evt-demo-001
INFO - Successfully processed: topic=user.login, event_id=evt-demo-001
WARNING - Duplicate detected: topic=user.login, event_id=evt-demo-001
```

**✅ Log menunjukkan:**
1. Event pertama diproses (INFO)
2. Event kedua ditolak sebagai duplicate (WARNING)

---

## 🔄 Step 3: Test Batch Publishing with Duplicates

### 3.1 Send Batch with Mix of New & Duplicate Events

```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "topic": "order.created",
        "event_id": "order-001",
        "timestamp": "2025-10-23T11:00:00Z",
        "source": "order-service",
        "payload": {"order_id": 1001, "amount": 100}
      },
      {
        "topic": "order.created",
        "event_id": "order-002",
        "timestamp": "2025-10-23T11:01:00Z",
        "source": "order-service",
        "payload": {"order_id": 1002, "amount": 200}
      },
      {
        "topic": "order.created",
        "event_id": "order-001",
        "timestamp": "2025-10-23T11:00:00Z",
        "source": "order-service",
        "payload": {"order_id": 1001, "amount": 100}
      }
    ]
  }'
```

**Expected response:**
```json
{
  "received": 3,
  "accepted": 2,
  "duplicates": 1
}
```

**📊 Analysis:**
- 3 events dikirim
- 2 events baru (order-001, order-002)
- 1 duplicate (order-001 muncul 2x dalam batch)

### 3.2 Verify Stats

```bash
curl http://localhost:8080/stats
```

**Expected changes:**
- `received`: +3
- `unique_processed`: +2
- `duplicate_dropped`: +1

---

## 🔥 Step 4: Crash Tolerance & Persistence Test

### 4.1 Send Events Before Restart

```bash
# Send unique event
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "payment.completed",
    "event_id": "pay-restart-001",
    "timestamp": "2025-10-23T12:00:00Z",
    "source": "payment-service",
    "payload": {"amount": 500, "currency": "USD"}
  }'
```

**Expected response:**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0
}
```

### 4.2 Verify Event Stored

```bash
curl "http://localhost:8080/events?topic=payment.completed"
```

**Expected output:**
```json
{
  "topic": "payment.completed",
  "count": 1,
  "events": [
    {
      "event_id": "pay-restart-001",
      ...
    }
  ]
}
```

### 4.3 Record Current Stats

```bash
# Save stats before restart
curl http://localhost:8080/stats > stats_before_restart.json
cat stats_before_restart.json
```

### 4.4 RESTART Container

```bash
# Restart container
docker restart log-aggregator

# Wait for restart (5 seconds)
sleep 5

# Check health
curl http://localhost:8080/health
```

**Expected health after restart:**
```json
{
  "status": "healthy",
  "consumer_running": true,
  "queue_size": 0
}
```

### 4.5 Send SAME Event After Restart

```bash
# Kirim event yang SAMA dengan sebelum restart
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "payment.completed",
    "event_id": "pay-restart-001",
    "timestamp": "2025-10-23T12:00:00Z",
    "source": "payment-service",
    "payload": {"amount": 500, "currency": "USD"}
  }'
```

**Expected response:**
```json
{
  "received": 1,
  "accepted": 0,
  "duplicates": 1
}
```

**✅ PROOF OF PERSISTENCE:**
Event yang diproses **sebelum restart** masih terdeteksi sebagai duplikat **setelah restart**!

### 4.6 Verify Database File Exists

```bash
# Check SQLite database file
ls -lh data/dedup.db

# Or on Windows
dir data\dedup.db
```

**Expected output:**
```
-rw-r--r-- 1 user user 12K Oct 23 12:05 data/dedup.db
```

### 4.7 Verify Events Persisted

```bash
curl "http://localhost:8080/events?topic=payment.completed"
```

**Expected output:**
```json
{
  "topic": "payment.completed",
  "count": 1,
  "events": [
    {
      "event_id": "pay-restart-001",
      ...
    }
  ]
}
```

**✅ Event masih ada setelah restart!**

### 4.8 Check Database Content (Optional)

```bash
# Install sqlite3 if not available
# sudo apt-get install sqlite3

# Query database directly
sqlite3 data/dedup.db "SELECT * FROM processed_events LIMIT 5;"
```

**Expected output:**
```
user.login|evt-demo-001|2025-10-23T10:00:00Z|demo-app|2025-10-23T10:00:15.123456
order.created|order-001|2025-10-23T11:00:00Z|order-service|2025-10-23T11:01:20.789012
order.created|order-002|2025-10-23T11:01:00Z|order-service|2025-10-23T11:01:20.890123
payment.completed|pay-restart-001|2025-10-23T12:00:00Z|payment-service|2025-10-23T12:00:30.456789
```

---

## 📊 Step 5: Performance Test with Scale

### 5.1 Run Performance Test

```bash
# Run 5000+ events test
python performance_test.py
```

**Expected summary:**
```
================================================================================
📊 PERFORMANCE TEST RESULTS
================================================================================

📤 Sending Statistics:
   • Total Events Sent: 5,000
   • Total Accepted: 3,750
   • Total Duplicates Detected: 1,250
   • Errors: 0
   • Duplication Rate: 25.00%

⚡ Performance Metrics:
   • Test Duration: 2.50s
   • Throughput: 2,000 events/s
   • Avg Response Time: 100.00ms
   • P95 Response Time: 150.00ms

✅ TEST VALIDATION:
   ✅ Event Count: 5,000 >= 5,000 (Required)
   ✅ Duplication Rate: 25.00% >= 20% (Required)
   ✅ Responsiveness: Avg 100ms < 1000ms (Target)
   ✅ System Health: healthy
```

---

## 🏗️ Step 6: Arsitektur & Design Decisions

### 6.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT / PUBLISHER                       │
│                   (HTTP POST /publish)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            POST /publish Endpoint                    │  │
│  │  • Pydantic validation                               │  │
│  │  • Quick dedup check (Phase 1)                       │  │
│  │  • Enqueue to EventQueue                             │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              EVENT QUEUE                             │  │
│  │  • In-memory asyncio.Queue                           │  │
│  │  • FIFO ordering guarantee                           │  │
│  │  • Max size: 10,000 events                           │  │
│  │  • Non-blocking async operations                     │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           EVENT CONSUMER                             │  │
│  │  • Background async task                             │  │
│  │  • Sequential processing (single consumer)           │  │
│  │  • Authoritative dedup check (Phase 2)               │  │
│  │  • Mark processed in DedupStore                      │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            DEDUP STORE                               │  │
│  │  • SQLite database (data/dedup.db)                   │  │
│  │  • PRIMARY KEY (topic, event_id)                     │  │
│  │  • ACID guarantees                                   │  │
│  │  • Persists across restarts                          │  │
│  │  • Docker volume mounted                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       QUERY ENDPOINTS                                │  │
│  │  • GET /events?topic=X (query by topic)              │  │
│  │  • GET /stats (metrics)                              │  │
│  │  • GET /health (health check)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Key Design Decisions

#### **1. Two-Phase Deduplication**

**Phase 1 - Quick Check (at /publish)**
```python
# Fast check to reject obvious duplicates early
if await dedup_store.is_duplicate(topic, event_id):
    duplicates += 1
    continue
await event_queue.enqueue(event)
```

**Phase 2 - Authoritative Check (at Consumer)**
```python
# Atomic check-and-set in SQLite
is_new = await dedup_store.mark_processed(topic, event_id, ...)
if not is_new:
    logger.warning(f"Duplicate: {topic}/{event_id}")
    continue
```

**Why?**
- ✅ Fast rejection prevents queue pollution
- ✅ Authoritative check ensures correctness
- ✅ Race conditions handled by SQLite constraint

#### **2. SQLite for Dedup Store**

**Alternatives Considered:**
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **SQLite** | Simple, ACID, file-based | Single node only | ✅ **CHOSEN** |
| Redis | Fast, distributed | External dependency | ❌ |
| PostgreSQL | Scalable, robust | Overkill for demo | ❌ |
| In-memory | Fastest | Lost on crash | ❌ |

**Why SQLite?**
```sql
CREATE TABLE processed_events (
    topic TEXT NOT NULL,
    event_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    PRIMARY KEY (topic, event_id)  -- ✅ Ensures uniqueness!
);
```

- ✅ `PRIMARY KEY` constraint prevents duplicates atomically
- ✅ ACID guarantees (Atomic, Consistent, Isolated, Durable)
- ✅ File-based persistence (survives restarts)
- ✅ No external dependencies
- ✅ Perfect for single-node deployment

#### **3. In-Memory Queue (asyncio.Queue)**

**Why not persist queue?**
- ✅ Events in queue are **transient** (not yet processed)
- ✅ If lost, publisher will retry (at-least-once delivery)
- ✅ Dedup store ensures idempotency
- ✅ High throughput, low latency

**Trade-off:**
- ❌ Queue lost on crash (before consumer processes)
- ✅ But: Events will be re-sent by publisher
- ✅ And: Already-processed events rejected by dedup store

#### **4. Single Consumer Pattern**

**Why single consumer?**
```python
# Background task in FastAPI lifespan
consumer = EventConsumer(event_queue, dedup_store)
asyncio.create_task(consumer.start())
```

- ✅ **No race conditions** (sequential processing)
- ✅ **FIFO ordering** guaranteed
- ✅ **Simpler logic** (no coordination needed)
- ✅ **Sufficient throughput** (2000+ events/s)

**When to scale?**
- If need >5000 events/s, consider:
  - Multiple consumers per topic
  - Partition by topic hash
  - External queue (RabbitMQ/Kafka)

#### **5. Crash Tolerance via Docker Volume**

```dockerfile
# Dockerfile
VOLUME /app/data
```

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data
```

```bash
# Run command
docker run -v $(pwd)/data:/app/data uts-aggregator
```

**Why?**
- ✅ SQLite file (`dedup.db`) persists on host
- ✅ Container restart doesn't lose data
- ✅ Easy backup (just copy `data/` directory)

#### **6. FastAPI Async/Await**

```python
@app.post("/publish")
async def publish(data: Union[Event, EventBatch]):
    async with asyncio.timeout(10):
        await event_queue.enqueue(event)
```

**Why async?**
- ✅ Non-blocking I/O (handle many requests)
- ✅ Efficient for I/O-bound operations
- ✅ Better throughput than sync
- ✅ Natural fit for asyncio.Queue

---

## 📋 Complete Demo Checklist

### Pre-Demo Setup
- [ ] Docker installed and running
- [ ] Port 8080 available
- [ ] `data/` directory for persistence
- [ ] curl or PowerShell available

### Demo Flow
- [ ] **Build** Docker image
- [ ] **Run** container
- [ ] **Verify** health endpoint
- [ ] **Check** initial stats (empty)
- [ ] **Send** first event
- [ ] **Verify** stats (1 processed)
- [ ] **Send** duplicate event
- [ ] **Verify** duplicate rejected
- [ ] **Check** stats (1 processed, 1 dropped)
- [ ] **Query** events by topic
- [ ] **Send** batch with duplicates
- [ ] **Restart** container
- [ ] **Send** old event again
- [ ] **Verify** persistence (still rejected)
- [ ] **Run** performance test (5000+ events)
- [ ] **Show** logs with warnings

### Key Points to Highlight
- ✅ **Idempotency**: Same event ID rejected
- ✅ **Deduplication**: 25% duplicates detected
- ✅ **Persistence**: Survives restart
- ✅ **Performance**: 2000+ events/s
- ✅ **Responsiveness**: <200ms latency
- ✅ **Simplicity**: Single container, no deps

---

## 🎓 Summary

**What We Demonstrated:**

1. ✅ **Build & Run**: Docker containerization dengan health checks
2. ✅ **Idempotency**: Event dengan `(topic, event_id)` sama hanya diproses sekali
3. ✅ **At-Least-Once**: Sistem handle duplicate submissions
4. ✅ **Stats Monitoring**: Real-time metrics via `/stats` endpoint
5. ✅ **Persistence**: SQLite database survive container restart
6. ✅ **Crash Tolerance**: Re-submit setelah restart tetap ditolak
7. ✅ **Performance**: 5000+ events dengan 25% duplikasi
8. ✅ **Arsitektur**: Two-phase dedup, FIFO queue, single consumer

**Technical Proof Points:**

| Requirement | Implementation | Proof |
|-------------|----------------|-------|
| Idempotency | SQLite PRIMARY KEY | `duplicates: 1` in response |
| Persistence | Docker volume + SQLite | Post-restart duplicate rejected |
| Performance | Async/await | 2000+ events/s |
| Deduplication | Two-phase check | 25% dup rate detected |
| Responsiveness | Non-blocking I/O | <200ms avg response |

---

**📖 For more details, see:**
- `ARCHITECTURE.md` - Deep dive arsitektur
- `PERFORMANCE_TEST.md` - Performance results
- `README.md` - API documentation
- `report.md` - Technical report
