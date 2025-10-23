# Quick Start Guide

## 🚀 Menjalankan Layanan dalam 3 Langkah

### Opsi 1: Docker Compose (Recommended)

```bash
# 1. Build dan jalankan service
docker-compose up -d

# 2. Lihat logs
docker-compose logs -f log-aggregator

# 3. Test dengan curl
curl http://localhost:8080/stats
```

### Opsi 2: Docker Manual

```bash
# 1. Build image
docker build -t log-aggregator:latest .

# 2. Run container
docker run -d --name log-aggregator -p 8080:8080 -v ${PWD}/data:/app/data log-aggregator:latest

# 3. Check status
docker logs -f log-aggregator
```

## 📝 Testing Cepat

### Test 1: Send Single Event

```bash
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": "user-123", "action": "login"}
  }'
```

**Expected Output:**
```json
{
  "received": 1,
  "accepted": 1,
  "duplicates": 0,
  "message": "Received 1 events, accepted 1, rejected 0 duplicates"
}
```

### Test 2: Send Duplicate (Idempotency Test)

```bash
# Send same event again
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user.login",
    "event_id": "evt-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "auth-service",
    "payload": {"user_id": "user-123", "action": "login"}
  }'
```

**Expected Output:**
```json
{
  "received": 1,
  "accepted": 0,
  "duplicates": 1,
  "message": "Received 1 events, accepted 0, rejected 1 duplicates"
}
```

### Test 3: Send Batch

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
      },
      {
        "topic": "order.created",
        "event_id": "order-002",
        "timestamp": "2025-10-23T10:06:00Z",
        "source": "order-service",
        "payload": {"order_id": "12346", "amount": 149.99}
      }
    ]
  }'
```

### Test 4: Check Statistics

```bash
curl http://localhost:8080/stats
```

**Expected Output:**
```json
{
  "received": 4,
  "unique_processed": 3,
  "duplicate_dropped": 1,
  "topics": ["user.login", "order.created"],
  "uptime_seconds": 120.5,
  "uptime_human": "0h 2m 0s"
}
```

### Test 5: Query Events by Topic

```bash
curl "http://localhost:8080/events?topic=user.login&limit=10"
```

### Test 6: Health Check

```bash
curl http://localhost:8080/health
```

## 🧪 Automated Testing

```bash
# Run test publisher (simulates at-least-once delivery with duplicates)
python test_publisher.py

# Or with Docker Compose
docker-compose --profile testing up publisher-simulator
```

## 🔄 Test Crash Tolerance

```bash
# 1. Send some events
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test.crash",
    "event_id": "crash-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "test",
    "payload": {}
  }'

# 2. Check stats
curl http://localhost:8080/stats

# 3. Restart container
docker-compose restart log-aggregator

# Wait a few seconds...
sleep 5

# 4. Send same event again
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test.crash",
    "event_id": "crash-001",
    "timestamp": "2025-10-23T10:00:00Z",
    "source": "test",
    "payload": {}
  }'

# 5. Should be rejected as duplicate!
curl http://localhost:8080/stats
```

**✅ Expected**: Event `crash-001` tetap ditolak setelah restart karena SQLite persistence.

## 📊 Monitoring Logs

```bash
# Watch logs in real-time
docker-compose logs -f log-aggregator

# Filter for duplicates
docker-compose logs log-aggregator | grep "Duplicate"

# Filter for processed events
docker-compose logs log-aggregator | grep "processed successfully"
```

## 🛑 Stop & Clean Up

```bash
# Stop services
docker-compose down

# Remove data (careful!)
rm -rf data/

# Remove images
docker rmi log-aggregator:latest
```

## 🐛 Troubleshooting

### Service tidak bisa diakses
```bash
# Check if running
docker ps | grep log-aggregator

# Check logs
docker-compose logs log-aggregator

# Check port
netstat -an | grep 8080
```

### Permission denied on data folder
```bash
# Fix permissions (Linux/Mac)
sudo chown -R $USER:$USER data/

# Windows: Run Docker Desktop as Administrator
```

### Database locked
```bash
# Restart service
docker-compose restart log-aggregator
```

## 📖 API Documentation

Setelah service berjalan, buka:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 💡 Tips

1. **Development Mode**: Edit file dan restart dengan `docker-compose restart`
2. **Production**: Gunakan volume terpisah untuk data persistence
3. **Scaling**: Bisa run multiple consumers dengan shared SQLite (or upgrade to PostgreSQL/Redis)
4. **Monitoring**: Integrate dengan Prometheus/Grafana untuk production monitoring

---

**Happy Testing! 🚀**
