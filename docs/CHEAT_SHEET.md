# 📝 Cheat Sheet - UTS Log Aggregator

Quick reference untuk command-command penting.

---

## 🚀 Quick Start

```bash
# Build image
docker build -t uts-aggregator .

# Run container
docker run -d -p 8080:8080 --name log-aggregator uts-aggregator

# With volume (persistence)
docker run -d -p 8080:8080 -v $(pwd)/data:/app/data --name log-aggregator uts-aggregator

# Using docker-compose
docker-compose up --build -d
```

---

## 🔧 Container Management

```bash
# Check status
docker ps

# View logs
docker logs log-aggregator

# Follow logs (real-time)
docker logs -f log-aggregator

# View last 50 lines
docker logs --tail 50 log-aggregator

# Restart container
docker restart log-aggregator

# Stop container
docker stop log-aggregator

# Remove container
docker rm log-aggregator

# Shell into container
docker exec -it log-aggregator /bin/bash

# Check container health
docker inspect log-aggregator | grep -A 10 Health
```

---

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "consumer_running": true,
  "queue_size": 0
}
```

### Publish Single Event
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "demo",
    "payload": {"user": "alice"}
  }'
```

**Response:**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0
}
```

### Publish Batch Events
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
        "payload": {"order_id": 1001}
      },
      {
        "topic": "order.created",
        "event_id": "order-002",
        "timestamp": "2025-10-23T11:01:00Z",
        "source": "order-service",
        "payload": {"order_id": 1002}
      }
    ]
  }'
```

### Get Statistics
```bash
curl http://localhost:8080/stats
```

**Response:**
```json
{
  "received": 100,
  "unique_processed": 75,
  "duplicate_dropped": 25,
  "topics": ["user.login", "order.created"],
  "uptime_seconds": 3600,
  "uptime_human": "01:00:00"
}
```

### Query Events by Topic
```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

**Response:**
```json
{
  "topic": "user.login",
  "count": 3,
  "events": [
    {
      "event_id": "evt-001",
      "timestamp": "2025-10-23T10:00:00Z",
      "source": "demo",
      "payload": {...}
    }
  ]
}
```

---

## 🧪 Testing Commands

### Unit Tests
```bash
# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_dedup_store.py -v

# Run core tests only (29 tests)
pytest tests/test_dedup_store.py tests/test_event_queue.py tests/test_models.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Performance Test
```bash
# Run 5000+ events with 25% duplication
python performance_test.py
```

### Integration Test
```bash
# Manual test publisher
python test_publisher.py
```

### Complete Demo (PowerShell)
```powershell
.\demo_complete.ps1
```

---

## 🔍 Troubleshooting Commands

### Check Service is Running
```bash
curl http://localhost:8080/health
```

### Check Logs for Errors
```bash
docker logs log-aggregator 2>&1 | grep ERROR
docker logs log-aggregator 2>&1 | grep WARNING
```

### Check Port is Open
```bash
# Linux/Mac
netstat -tuln | grep 8080

# Windows
netstat -an | findstr :8080
```

### Check Database File
```bash
# List database file
ls -lh data/dedup.db

# Windows
dir data\dedup.db

# Query database directly
sqlite3 data/dedup.db "SELECT COUNT(*) FROM processed_events;"
sqlite3 data/dedup.db "SELECT * FROM processed_events LIMIT 5;"
```

### Check Container Resources
```bash
docker stats log-aggregator --no-stream
```

---

## 🧹 Cleanup Commands

```bash
# Stop and remove container
docker stop log-aggregator
docker rm log-aggregator

# Remove image
docker rmi uts-aggregator

# Remove volume data (⚠️ CAUTION: Deletes all data)
rm -rf data/

# Full cleanup
docker stop log-aggregator
docker rm log-aggregator
docker rmi uts-aggregator
rm -rf data/
```

---

## 📊 Demo Scenarios

### Demo 1: Idempotency Test
```bash
# 1. Send event first time
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{"topic":"test","event_id":"test-1","timestamp":"2025-10-23T10:00:00Z","source":"demo","payload":{}}'

# Expected: {"received":1,"accepted":1,"duplicates":0}

# 2. Send SAME event again
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{"topic":"test","event_id":"test-1","timestamp":"2025-10-23T10:00:00Z","source":"demo","payload":{}}'

# Expected: {"received":1,"accepted":0,"duplicates":1}
```

### Demo 2: Persistence Test
```bash
# 1. Send event
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{"topic":"persist","event_id":"persist-1","timestamp":"2025-10-23T10:00:00Z","source":"demo","payload":{}}'

# 2. Restart container
docker restart log-aggregator
sleep 5

# 3. Send SAME event after restart
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{"topic":"persist","event_id":"persist-1","timestamp":"2025-10-23T10:00:00Z","source":"demo","payload":{}}'

# Expected: {"received":1,"accepted":0,"duplicates":1}
# ✅ Persistence working!
```

### Demo 3: Stats Monitoring
```bash
# Get stats before
curl http://localhost:8080/stats > before.json
cat before.json

# Send events
for i in {1..10}; do
  curl -X POST http://localhost:8080/publish \
    -H "Content-Type: application/json" \
    -d "{\"topic\":\"demo\",\"event_id\":\"evt-$i\",\"timestamp\":\"2025-10-23T10:00:00Z\",\"source\":\"demo\",\"payload\":{}}"
done

# Get stats after
curl http://localhost:8080/stats > after.json
cat after.json

# Compare
diff before.json after.json
```

---

## 🎯 PowerShell Commands (Windows)

### Build & Run
```powershell
# Build
docker build -t uts-aggregator .

# Run with volume
docker run -d -p 8080:8080 -v ${PWD}/data:/app/data --name log-aggregator uts-aggregator

# Check health
Invoke-RestMethod -Uri "http://localhost:8080/health"
```

### Send Event
```powershell
$body = @{
    topic = "user.login"
    event_id = "evt-001"
    timestamp = (Get-Date -Format "o")
    source = "powershell"
    payload = @{user = "alice"}
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -Body $body -ContentType "application/json"
```

### Get Stats
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/stats" | ConvertTo-Json -Depth 10
```

### Query Events
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/events?topic=user.login&limit=10" | ConvertTo-Json -Depth 10
```

---

## 📚 File Locations

```
Project Root/
├── src/                      # Application code
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── dedup_store.py       # SQLite dedup
│   ├── event_queue.py       # Async queue
│   └── consumer.py          # Event consumer
│
├── tests/                    # Unit tests
│   ├── test_dedup_store.py  # 10 tests
│   ├── test_event_queue.py  # 8 tests
│   └── test_models.py       # 11 tests
│
├── data/                     # Persisted data
│   └── dedup.db            # SQLite database
│
├── Dockerfile               # Container definition
├── docker-compose.yml       # Orchestration
├── requirements.txt         # Python dependencies
│
├── DEMO_GUIDE.md           # Step-by-step demo
├── ARCHITECTURE.md         # Design deep dive
├── ARCHITECTURE_SUMMARY.md # Quick reference
├── PERFORMANCE_TEST.md     # Test results
├── CHEAT_SHEET.md         # This file
│
├── performance_test.py     # 5K events test
├── test_publisher.py       # Manual tester
└── demo_complete.ps1       # Automated demo
```

---

## 🎓 Key Metrics to Show

```bash
# 1. Health Status
curl http://localhost:8080/health

# 2. Statistics
curl http://localhost:8080/stats

# 3. Topics
curl http://localhost:8080/stats | jq '.topics'

# 4. Duplication Rate
curl http://localhost:8080/stats | jq '{received, unique_processed, duplicate_dropped, rate: (.duplicate_dropped / .received * 100)}'

# 5. Event Count by Topic
curl "http://localhost:8080/events?topic=user.login" | jq '.count'
```

---

## 🔑 Important Notes

- **Port**: Default 8080
- **Database**: `data/dedup.db` (persisted)
- **Volume**: Mount `./data:/app/data` for persistence
- **Dedup Key**: `(topic, event_id)` must be unique
- **Timestamp**: Must be ISO8601 format
- **Max Queue**: 10,000 events
- **Throughput**: ~2,000 events/second

---

## 📞 Quick Reference URLs

- Health: `http://localhost:8080/health`
- Stats: `http://localhost:8080/stats`
- Publish: `POST http://localhost:8080/publish`
- Events: `http://localhost:8080/events?topic=X&limit=N`
- API Docs: `http://localhost:8080/docs` (Swagger)
- ReDoc: `http://localhost:8080/redoc`

---

**💡 Tip**: Save this file for quick reference during demos!
