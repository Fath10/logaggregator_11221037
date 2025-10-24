# Log Aggregator Service - Pub/Sub dengan Idempotency & Deduplication

🎥 **Video Demo**: [Tonton di YouTube](https://youtu.be/qVEZrpUy-2Q?si=CZMbD9Rv7Gsf5ckd)
📄 **PDF Teori**: [Link_Drive] (https://drive.google.com/file/d/12pRvQV7InDwCyR1EMXm9JFL6bUXJzAxo/view?usp=sharing)

## 📋 Deskripsi

Layanan **Log Aggregator** berbasis Python (FastAPI + asyncio) yang mengimplementasikan pola Pub-Sub dengan fitur:
- ✅ **Idempotent Processing**: Setiap event dengan `(topic, event_id)` yang sama hanya diproses sekali
- ✅ **Deduplication**: Deteksi dan penolakan event duplikat secara otomatis
- ✅ **At-least-once Delivery**: Simulasi pengiriman duplikat untuk validasi
- ✅ **Crash Tolerance**: Persistence menggunakan SQLite, data tetap tersimpan setelah restart
- ✅ **In-memory Queue**: Async processing dengan asyncio.Queue
- ✅ **RESTful API**: Endpoint untuk publish, query, dan monitoring
- ✅ **Docker Support**: Dockerfile dan Docker Compose siap production

## 🚀 Quick Start

### Cara 1: Docker (Recommended)

#### Build Image
```bash
docker build -t uts-aggregator .
```

#### Run Container
```bash
docker run -p 8080:8080 uts-aggregator
```

#### Dengan Volume untuk Persistence
```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data uts-aggregator
```

### Cara 2: Docker Compose (Bonus)

```bash
# Build dan jalankan
docker-compose up -d

# Lihat logs
docker-compose logs -f log-aggregator

# Stop
docker-compose down
```

### Cara 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Buat data directory
mkdir -p data

# Run aplikasi
python src/main.py
```

---

## 📡 API Endpoints

### 1. POST /publish
Menerima single event atau batch events dengan validasi schema.

**Single Event:**
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": "user-123"}
  }'
```

**Response:**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0,
  "message": "Received 1 events, accepted 1, rejected 0 duplicates"
}
```

**Batch Events:**
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "topic": "order.created",
        "event_id": "order-001",
        "timestamp": "2025-10-23T10:05:00Z",
        "source": "order-service",
        "payload": {"order_id": "12345", "amount": 99.99}
      }
    ]
  }'
```

### 2. GET /events?topic={topic}&limit={limit}
Query events yang telah diproses berdasarkan topic.

```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

**Response:**
```json
{
  "topic": "user.login",
  "count": 5,
  "events": [
    {
      "topic": "user.login",
      "event_id": "evt-001",
      "timestamp": "2025-10-23T10:00:00Z",
      "source": "auth-service",
      "payload": {"processed_at": "2025-10-23T10:00:01.123456"}
    }
  ]
}
```

### 3. GET /stats
Mendapatkan statistik layanan secara real-time.

```bash
curl http://localhost:8080/stats
```

**Response:**
```json
{
  "received": 150,
  "unique_processed": 120,
  "duplicate_dropped": 30,
  "topics": ["user.login", "order.created", "payment.processed"],
  "uptime_seconds": 3600.5,
  "uptime_human": "1h 0m 0s"
}
```

### 4. GET /health
Health check endpoint untuk monitoring.

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "consumer_running": true,
  "queue_size": 0,
  "timestamp": "2025-10-23T10:30:45.123456"
}
```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_dedup_store.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Test Publisher (Integration Test)
```bash
python test_publisher.py
```

---

## 📊 Event Schema

```json
{
  "topic": "string (required, min: 1, max: 255)",
  "event_id": "string (required, min: 1, max: 255)",
  "timestamp": "string (required, ISO8601 format)",
  "source": "string (required, min: 1, max: 255)",
  "payload": "object (optional, flexible structure)"
}
```

**Contoh Valid:**
```json
{
  "topic": "user.login",
  "event_id": "evt-12345-abcde",
  "timestamp": "2025-10-23T10:30:00Z",
  "source": "auth-service",
  "payload": {
    "user_id": "user-123",
    "ip_address": "192.168.1.1",
    "success": true
  }
}
```

---

## 🔧 Konfigurasi

### Environment Variables

```bash
# Log level
export LOG_LEVEL=INFO

# Database path
export DATABASE_PATH=data/dedup.db

# Server port
export PORT=8080
```

### Docker Environment
```bash
docker run -p 8080:8080 \
  -e LOG_LEVEL=DEBUG \
  -e DATABASE_PATH=data/dedup.db \
  uts-aggregator
```

---

## 🏗️ Struktur Project

```
.
├── src/                        # Source code aplikasi
│   ├── __init__.py
│   ├── main.py                 # FastAPI app & endpoints
│   ├── models.py               # Pydantic models
│   ├── event_queue.py          # In-memory queue
│   ├── dedup_store.py          # SQLite persistence
│   └── consumer.py             # Event consumer
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── test_api.py            # API endpoint tests
│   ├── test_dedup_store.py    # DedupStore tests
│   ├── test_event_queue.py    # EventQueue tests
│   └── test_models.py         # Model validation tests
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Orchestration (bonus)
├── requirements.txt            # Python dependencies
├── test_publisher.py           # Integration test script
├── README.md                   # Documentation (this file)
└── report.md                   # Design report
```

---

## 🔍 Asumsi dan Design Decisions

### 1. **Deduplication Key**
- **Asumsi**: Event unik ditentukan oleh kombinasi `(topic, event_id)`
- **Rationale**: Memungkinkan event_id yang sama di topic berbeda
- **Implementation**: SQLite `PRIMARY KEY (topic, event_id)`

### 2. **Ordering**
- **Asumsi**: Total ordering tidak diperlukan untuk log aggregation
- **Rationale**: Event independen, idempotency membuat order tidak critical
- **Implementation**: FIFO per-topic dari queue, no global ordering

### 3. **Persistence**
- **Asumsi**: SQLite cukup untuk single-instance deployment
- **Rationale**: Lightweight, ACID compliant, no external dependencies
- **Limitation**: Single writer, not suitable for distributed setup

### 4. **Queue**
- **Asumsi**: In-memory queue dengan asyncio.Queue
- **Rationale**: Low latency, suitable untuk medium throughput
- **Limitation**: Data lost on crash (mitigated by dedup check at publish)

### 5. **Consumer Model**
- **Asumsi**: Single consumer thread cukup untuk demo
- **Rationale**: Simplicity, predictable behavior
- **Scaling**: Bisa di-scale dengan multiple consumers + distributed dedup store

### 6. **Error Handling**
- **Asumsi**: Consumer continues on individual event errors
- **Rationale**: One bad event shouldn't stop entire pipeline
- **Implementation**: Try-catch per event, logging errors

### 7. **Payload Storage**
- **Asumsi**: Hanya metadata yang disimpan di SQLite
- **Rationale**: Keep dedup store lightweight
- **Alternative**: Bisa store full payload jika needed

---

## 🚨 Limitations & Known Issues

1. **Batch Duplicate Reporting**: Response dari batch publish mungkin tidak akurat untuk internal duplicates karena consumer async
2. **Single Consumer**: Throughput terbatas ~1000 events/sec
3. **SQLite**: Single writer limitation, not for high-concurrency
4. **In-memory Queue**: Lost on crash (before processing)
5. **No Authentication**: API terbuka, perlu auth untuk production

---

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Throughput | ~1000 events/sec (single consumer) |
| Latency (publish) | <10ms |
| Latency (process) | <50ms |
| Memory | ~50MB base + O(n) queue |
| Storage | ~1KB per unique event |

---

## 🐛 Troubleshooting

### Container tidak start
```bash
# Check logs
docker logs log-aggregator

# Check permissions
ls -la data/
```

### Port already in use
```bash
# Use different port
docker run -p 8081:8080 uts-aggregator
```

### Database locked
```bash
# Restart container
docker restart log-aggregator
```

---

## 📚 Dokumentasi Lengkap

- **README.md** - Setup dan API documentation (file ini)
- **report.md** - Design decisions dan analisis teknis
- **TECHNICAL_REPORT.md** - Analisis mendalam

---

## 👨‍💻 Development

### Run with Auto-reload
```bash
python -m uvicorn src.main:app --reload
```

### Run Tests
```bash
pytest tests/ -v
```

### API Documentation (Auto-generated)
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## 🔐 Production Recommendations

1. **Add Authentication**: Implement API keys atau OAuth
2. **Use PostgreSQL**: Replace SQLite untuk distributed setup
3. **Add Message Broker**: RabbitMQ/Kafka untuk persistent queue
4. **Monitoring**: Prometheus + Grafana
5. **Logging**: Structured JSON logging ke ELK/Splunk
6. **Rate Limiting**: Protect against abuse
7. **HTTPS**: SSL/TLS termination
8. **Horizontal Scaling**: Multiple instances + load balancer

---

## 📄 License

MIT License - Free untuk educational purposes.

---

## 🙋 Support

Untuk pertanyaan atau issues:
1. Check logs: `docker logs log-aggregator`
2. Check health: `curl http://localhost:8080/health`
3. Check stats: `curl http://localhost:8080/stats`

---


```
┌─────────────┐
│  Publisher  │
│  (Client)   │
└──────┬──────┘
       │ HTTP POST /publish
       ▼
┌─────────────────────────────────────────┐
│         Log Aggregator Service          │
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │   FastAPI   │───▶│  EventQueue    │ │
│  │  Endpoint   │    │  (in-memory)   │ │
│  └─────────────┘    └────────┬───────┘ │
│                              │         │
│                              ▼         │
│  ┌──────────────────────────────────┐ │
│  │      EventConsumer (async)       │ │
│  │  • Dequeue events                │ │
│  │  • Check DedupStore              │ │
│  │  • Process if unique             │ │
│  └──────────────┬───────────────────┘ │
│                 │                      │
│                 ▼                      │
│  ┌──────────────────────────────────┐ │
│  │  DedupStore (SQLite)             │ │
│  │  • Track (topic, event_id)       │ │
│  │  • Persist to disk               │ │
│  │  • Survive restarts              │ │
│  └──────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🚀 Fitur Utama

### 1. Event Schema
```json
{
  "topic": "user.login",
  "event_id": "evt-12345-abcde",
  "timestamp": "2025-10-23T10:30:00Z",
  "source": "auth-service",
  "payload": {
    "user_id": "user-123",
    "ip_address": "192.168.1.1",
    "success": true
  }
}
```

### 2. API Endpoints

#### POST /publish
Menerima single event atau batch events dengan validasi schema.

**Single Event:**
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": "user-123"}
  }'
```

**Batch Events:**
```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "topic": "user.login",
        "event_id": "evt-001",
        "timestamp": "2025-10-23T10:00:00Z",
        "source": "auth-service",
        "payload": {"user_id": "user-123"}
      },
      {
        "topic": "order.created",
        "event_id": "evt-002",
        "timestamp": "2025-10-23T10:01:00Z",
        "source": "order-service",
        "payload": {"order_id": "ord-456"}
      }
    ]
  }'
```

**Response:**
```json
{
  "received": 2,
  "accepted": 2,
  "duplicates": 0,
  "message": "Received 2 events, accepted 2, rejected 0 duplicates"
}
```

#### GET /events?topic=...
Query events yang telah diproses berdasarkan topic.

```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

**Response:**
```json
{
  "topic": "user.login",
  "count": 5,
  "events": [
    {
      "topic": "user.login",
      "event_id": "evt-001",
      "timestamp": "2025-10-23T10:00:00Z",
      "source": "auth-service",
      "payload": {"processed_at": "2025-10-23T10:00:01.123456"}
    }
  ]
}
```

#### GET /stats
Mendapatkan statistik layanan secara real-time.

```bash
curl http://localhost:8080/stats
```

**Response:**
```json
{
  "received": 150,
  "unique_processed": 120,
  "duplicate_dropped": 30,
  "topics": ["user.login", "order.created", "payment.processed"],
  "uptime_seconds": 3600.5,
  "uptime_human": "1h 0m 0s"
}
```

#### GET /health
Health check endpoint untuk monitoring.

```bash
curl http://localhost:8080/health
```

## 🐳 Menjalankan dengan Docker

### Build & Run (Docker)

```bash
# Build image
docker build -t log-aggregator:latest .

# Run container
docker run -d \
  --name log-aggregator \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  log-aggregator:latest

# Check logs
docker logs -f log-aggregator
```

### Build & Run (Docker Compose)

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f log-aggregator

# Stop service
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Run dengan Publisher Simulator (Testing)

```bash
# Run with test publisher
docker-compose --profile testing up -d

# Check publisher logs
docker-compose logs -f publisher-simulator
```

## 🧪 Testing

### Manual Testing

```bash
# 1. Start service
docker-compose up -d

# 2. Send test event
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test.event",
    "event_id": "test-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "manual-test",
    "payload": {"test": true}
  }'

# 3. Send duplicate (should be rejected)
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test.event",
    "event_id": "test-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "manual-test",
    "payload": {"test": true}
  }'

# 4. Check stats
curl http://localhost:8080/stats

# 5. Query events
curl "http://localhost:8080/events?topic=test.event"
```

### Automated Testing dengan Publisher Simulator

```bash
# Run publisher simulator
python test_publisher.py
```

Simulator akan:
- ✅ Mengirim event yang sama 3 kali (test retry)
- ✅ Mengirim batch dengan duplikat internal
- ✅ Mengirim batch campuran (baru + duplikat)
- ✅ Test multiple topics
- ✅ High-frequency publishing dengan duplikat acak

## 🔄 Testing Crash Tolerance

### Scenario 1: Restart Container

```bash
# 1. Send events
curl -X POST http://localhost:8080/publish -H "Content-Type: application/json" \
  -d '{"topic": "test", "event_id": "evt-001", "timestamp": "2025-10-23T10:00:00Z", "source": "test", "payload": {}}'

# 2. Check stats (note unique_processed count)
curl http://localhost:8080/stats

# 3. Restart container
docker-compose restart log-aggregator

# 4. Send same event again
curl -X POST http://localhost:8080/publish -H "Content-Type: application/json" \
  -d '{"topic": "test", "event_id": "evt-001", "timestamp": "2025-10-23T10:00:00Z", "source": "test", "payload": {}}'

# 5. Verify it's rejected as duplicate
curl http://localhost:8080/stats
```

**Expected Result**: Event `evt-001` tetap ditolak sebagai duplikat setelah restart karena SQLite menyimpan state.

### Scenario 2: Stop & Start Container

```bash
# Stop container
docker-compose down

# Start again
docker-compose up -d

# Send previously sent event
curl -X POST http://localhost:8080/publish -H "Content-Type: application/json" \
  -d '{"topic": "test", "event_id": "evt-001", "timestamp": "2025-10-23T10:00:00Z", "source": "test", "payload": {}}'

# Should be rejected
curl http://localhost:8080/stats
```

## 📊 Idempotency & Deduplication

### Cara Kerja

1. **Publisher** mengirim event ke endpoint `/publish`
2. **FastAPI Handler** melakukan validasi schema dan quick dedup check
3. Event yang valid di-enqueue ke **EventQueue** (in-memory)
4. **EventConsumer** (background async task) meng-dequeue event
5. Consumer memeriksa **DedupStore** (SQLite):
   - Jika `(topic, event_id)` sudah ada → **REJECT** (log duplicate)
   - Jika belum ada → **ACCEPT** dan mark as processed
6. SQLite constraint `PRIMARY KEY (topic, event_id)` menjamin atomicity

### Dedup Store (SQLite)

```sql
CREATE TABLE processed_events (
    topic TEXT NOT NULL,
    event_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    PRIMARY KEY (topic, event_id)
);
```

**Keuntungan SQLite:**
- ✅ Persist to disk (survive restart)
- ✅ ACID compliance (atomic operations)
- ✅ No external dependencies
- ✅ Lightweight & fast
- ✅ File-based (easy backup)

### Log Output untuk Duplicate Detection

```
2025-10-23 10:30:15 - src.consumer - WARNING - Duplicate event detected and dropped: topic=user.login, event_id=evt-001, source=auth-service
```

## 📈 Ordering & Consistency

### Total Ordering: Tidak Diperlukan

Dalam konteks log aggregator ini, **total ordering TIDAK diperlukan** karena:

1. **Event Independence**: Setiap event adalah atomic unit yang independen
2. **Idempotency**: Processing order tidak mempengaruhi hasil akhir
3. **Distributed Nature**: Publisher bisa mengirim dari berbagai sumber secara parallel
4. **Scalability**: Tidak perlu koordinasi global untuk ordering

### Partial Ordering: Cukup

Yang diperlukan adalah **partial ordering per topic**:
- Events dalam topic yang sama diproses FIFO dari queue
- Timestamps digunakan untuk reference temporal, bukan strict ordering
- Deduplication berdasarkan `(topic, event_id)` bukan timestamp

### Trade-offs

| Aspect | Total Ordering | No Total Ordering (Current) |
|--------|----------------|----------------------------|
| Throughput | Low | High ✅ |
| Latency | High | Low ✅ |
| Complexity | High | Low ✅ |
| Scalability | Limited | Unlimited ✅ |
| Use Case | Financial transactions | Log aggregation ✅ |

**Kesimpulan**: Untuk log aggregation dengan idempotency, ordering flexibility memberikan better performance dan scalability tanpa mengorbankan correctness.

## 🔧 Konfigurasi

### Environment Variables

```bash
# .env file (optional)
LOG_LEVEL=INFO
DATABASE_PATH=data/dedup.db
QUEUE_MAX_SIZE=10000
PORT=8080
```

### Docker Compose dengan Environment

```yaml
services:
  log-aggregator:
    environment:
      - LOG_LEVEL=DEBUG
      - PYTHONUNBUFFERED=1
```

## 📁 Struktur Project

```
.
├── Dockerfile                  # Main service container
├── Dockerfile.publisher        # Test publisher container
├── docker-compose.yml          # Orchestration
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation (this file)
├── test_publisher.py           # Test publisher script
├── data/                       # SQLite database (persisted)
│   └── dedup.db
└── src/
    ├── __init__.py
    ├── main.py                 # FastAPI application
    ├── models.py               # Pydantic models
    ├── event_queue.py          # In-memory queue
    ├── dedup_store.py          # SQLite dedup storage
    └── consumer.py             # Event consumer/processor
```

## 🛡️ Security Best Practices

- ✅ Non-root user dalam container
- ✅ Minimal base image (python:3.11-slim)
- ✅ Dependencies pinned dengan version
- ✅ Health checks enabled
- ✅ Volume untuk data persistence
- ✅ No hardcoded secrets

## 📝 Dependencies

```txt
fastapi==0.104.1           # Web framework
uvicorn[standard]==0.24.0  # ASGI server
pydantic==2.5.0            # Data validation
aiosqlite==0.19.0          # Async SQLite
python-dateutil==2.8.2     # Date handling
```

## 🚀 Production Considerations

### Scaling

Untuk production dengan high throughput:
1. **Replace SQLite** dengan Redis/PostgreSQL untuk distributed dedup
2. **Add message broker** (RabbitMQ/Kafka) untuk persistent queue
3. **Multiple consumers** dengan load balancing
4. **Horizontal scaling** dengan container orchestration (Kubernetes)

### Monitoring

```bash
# Prometheus metrics endpoint (future enhancement)
GET /metrics

# Structured logging untuk ELK/Splunk
JSON formatted logs
```

### Backup

```bash
# Backup SQLite database
docker exec log-aggregator sqlite3 /app/data/dedup.db ".backup /app/data/backup.db"

# Volume backup
docker run --rm -v log-aggregator_data:/data -v $(pwd):/backup alpine tar czf /backup/dedup-backup.tar.gz /data
```

## 📖 Laporan Teknis

### At-least-once Delivery Simulation

Test publisher (`test_publisher.py`) mensimulasikan:
- **Retry mechanism**: Event yang sama dikirim 3x
- **Network duplicates**: Batch dengan event duplikat
- **Mixed batches**: Kombinasi event baru + duplikat

**Hasil yang diharapkan**:
- `received` = total semua event diterima
- `unique_processed` = hanya event unik yang diproses
- `duplicate_dropped` = jumlah duplikat yang ditolak

### Crash Tolerance

SQLite database di-persist melalui Docker volume:
```yaml
volumes:
  - ./data:/app/data
```

**Mekanisme**:
1. Setiap event yang diproses dicatat di SQLite
2. SQLite file disimpan di volume persisten
3. Setelah restart, service membaca state dari SQLite
4. Duplicate event tetap ditolak meski container restart

**Test**: Jalankan scenario testing di bagian "Testing Crash Tolerance"

### Performance

| Metric | Value |
|--------|-------|
| Throughput | ~1000 events/sec (single consumer) |
| Latency | <10ms (publish) + <50ms (processing) |
| Memory | ~50MB base + O(n) queue |
| Storage | ~1KB per unique event (SQLite) |

## 🐛 Troubleshooting

### Container tidak start

```bash
# Check logs
docker-compose logs log-aggregator

# Check database permissions
ls -la data/
```

### Events tidak diproses

```bash
# Check consumer status
curl http://localhost:8080/health

# Check queue size
curl http://localhost:8080/stats | jq '.queue_size'
```

### Database locked

```bash
# Restart container
docker-compose restart log-aggregator
```

## 👨‍💻 Development

### Local Development (tanpa Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run service
python -m uvicorn src.main:app --reload --port 8080

# Run tests
python test_publisher.py
```

## 📜 License

MIT License - Free to use for educational purposes.

## 🙋 Support

Untuk pertanyaan atau issues:
1. Check logs: `docker-compose logs -f`
2. Check health: `curl http://localhost:8080/health`
3. Check stats: `curl http://localhost:8080/stats`

---

**Built with ❤️ using FastAPI + Python + Docker**
