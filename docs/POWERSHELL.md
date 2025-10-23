# PowerShell Scripts untuk Windows

## Build dan Run

```powershell
# Build image
docker build -t log-aggregator:latest .

# Run container dengan volume mounting
docker run -d `
  --name log-aggregator `
  -p 8080:8080 `
  -v ${PWD}/data:/app/data `
  log-aggregator:latest

# Check logs
docker logs -f log-aggregator
```

## Docker Compose

```powershell
# Start services
docker-compose up -d

# View logs
docker-compose logs -f log-aggregator

# Stop services
docker-compose down
```

## Testing Scripts

### Test 1: Single Event
```powershell
$body = @{
    topic = "user.login"
    event_id = "evt-001"
    timestamp = "2025-10-23T10:00:00Z"
    source = "auth-service"
    payload = @{
        user_id = "user-123"
        action = "login"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/publish" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Test 2: Duplicate Event
```powershell
# Send same event again - should be rejected
Invoke-RestMethod -Uri "http://localhost:8080/publish" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Test 3: Batch Events
```powershell
$batch = @{
    events = @(
        @{
            topic = "order.created"
            event_id = "order-001"
            timestamp = "2025-10-23T10:05:00Z"
            source = "order-service"
            payload = @{
                order_id = "12345"
                amount = 99.99
            }
        },
        @{
            topic = "order.created"
            event_id = "order-002"
            timestamp = "2025-10-23T10:06:00Z"
            source = "order-service"
            payload = @{
                order_id = "12346"
                amount = 149.99
            }
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8080/publish" `
    -Method Post `
    -ContentType "application/json" `
    -Body $batch
```

### Test 4: Get Stats
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/stats" -Method Get | ConvertTo-Json
```

### Test 5: Query Events
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/events?topic=user.login&limit=10" -Method Get | ConvertTo-Json -Depth 10
```

### Test 6: Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get | ConvertTo-Json
```

## Complete Test Script

```powershell
# Complete-Test.ps1
Write-Host "=== Log Aggregator Test Suite ===" -ForegroundColor Cyan

# Test 1: Single Event
Write-Host "`n[Test 1] Sending single event..." -ForegroundColor Yellow
$event1 = @{
    topic = "user.login"
    event_id = "evt-$(Get-Random -Maximum 9999)"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "powershell-test"
    payload = @{ test = $true }
} | ConvertTo-Json

$result1 = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $event1
Write-Host "Result: Received=$($result1.received), Accepted=$($result1.accepted), Duplicates=$($result1.duplicates)" -ForegroundColor Green

# Test 2: Duplicate
Write-Host "`n[Test 2] Sending duplicate..." -ForegroundColor Yellow
$result2 = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $event1
Write-Host "Result: Received=$($result2.received), Accepted=$($result2.accepted), Duplicates=$($result2.duplicates)" -ForegroundColor Green

# Test 3: Batch
Write-Host "`n[Test 3] Sending batch..." -ForegroundColor Yellow
$batch = @{
    events = @(
        @{
            topic = "test.batch"
            event_id = "batch-$(Get-Random)"
            timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            source = "powershell-test"
            payload = @{ index = 1 }
        },
        @{
            topic = "test.batch"
            event_id = "batch-$(Get-Random)"
            timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            source = "powershell-test"
            payload = @{ index = 2 }
        }
    )
} | ConvertTo-Json -Depth 10

$result3 = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $batch
Write-Host "Result: Received=$($result3.received), Accepted=$($result3.accepted), Duplicates=$($result3.duplicates)" -ForegroundColor Green

# Test 4: Stats
Write-Host "`n[Test 4] Getting statistics..." -ForegroundColor Yellow
$stats = Invoke-RestMethod -Uri "http://localhost:8080/stats" -Method Get
Write-Host "Stats:" -ForegroundColor Green
Write-Host "  Received: $($stats.received)"
Write-Host "  Unique Processed: $($stats.unique_processed)"
Write-Host "  Duplicates Dropped: $($stats.duplicate_dropped)"
Write-Host "  Topics: $($stats.topics -join ', ')"
Write-Host "  Uptime: $($stats.uptime_human)"

# Test 5: Query
Write-Host "`n[Test 5] Querying events..." -ForegroundColor Yellow
$events = Invoke-RestMethod -Uri "http://localhost:8080/events?topic=user.login&limit=5" -Method Get
Write-Host "Found $($events.count) events for topic 'user.login'" -ForegroundColor Green

# Test 6: Health
Write-Host "`n[Test 6] Health check..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get
Write-Host "Status: $($health.status), Consumer Running: $($health.consumer_running), Queue Size: $($health.queue_size)" -ForegroundColor Green

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
```

## Crash Tolerance Test

```powershell
# Crash-Test.ps1
Write-Host "=== Crash Tolerance Test ===" -ForegroundColor Cyan

# 1. Send event
Write-Host "`n[1] Sending test event..." -ForegroundColor Yellow
$testEvent = @{
    topic = "crash.test"
    event_id = "crash-persistent-001"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "crash-test"
    payload = @{ test = "persistence" }
} | ConvertTo-Json

$result1 = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $testEvent
Write-Host "Result: Accepted=$($result1.accepted)" -ForegroundColor Green

# 2. Get stats before restart
Write-Host "`n[2] Stats before restart..." -ForegroundColor Yellow
$statsBefore = Invoke-RestMethod -Uri "http://localhost:8080/stats" -Method Get
Write-Host "Unique Processed: $($statsBefore.unique_processed)" -ForegroundColor Green

# 3. Restart container
Write-Host "`n[3] Restarting container..." -ForegroundColor Yellow
docker-compose restart log-aggregator
Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 4. Wait for health check
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get -ErrorAction SilentlyContinue
        if ($health.status -eq "healthy") {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "Service not ready after 30 seconds!" -ForegroundColor Red
    exit 1
}

Write-Host "Service is ready!" -ForegroundColor Green

# 5. Send same event again
Write-Host "`n[4] Sending same event after restart..." -ForegroundColor Yellow
$result2 = Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $testEvent
Write-Host "Result: Accepted=$($result2.accepted), Duplicates=$($result2.duplicates)" -ForegroundColor Green

# 6. Verify duplicate was rejected
if ($result2.duplicates -eq 1 -and $result2.accepted -eq 0) {
    Write-Host "`n✅ SUCCESS: Event was correctly identified as duplicate after restart!" -ForegroundColor Green
} else {
    Write-Host "`n❌ FAILED: Event should have been rejected as duplicate!" -ForegroundColor Red
}

# 7. Get final stats
Write-Host "`n[5] Final stats..." -ForegroundColor Yellow
$statsAfter = Invoke-RestMethod -Uri "http://localhost:8080/stats" -Method Get
Write-Host "Unique Processed: $($statsAfter.unique_processed)" -ForegroundColor Green
Write-Host "Duplicates Dropped: $($statsAfter.duplicate_dropped)" -ForegroundColor Green

Write-Host "`n=== Crash Tolerance Test Complete ===" -ForegroundColor Cyan
```

## How to Run Scripts

### Option 1: Copy-paste commands directly into PowerShell

### Option 2: Save as .ps1 file and run

```powershell
# Save as Complete-Test.ps1 then run:
.\Complete-Test.ps1

# Save as Crash-Test.ps1 then run:
.\Crash-Test.ps1
```

### Option 3: Run inline

```powershell
# Quick test
$body = @{
    topic = "quick.test"
    event_id = "quick-$(Get-Random)"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "powershell"
    payload = @{}
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $body | Format-List
```

## Monitoring Commands

```powershell
# Watch logs continuously (Ctrl+C to stop)
docker logs -f log-aggregator

# Get last 50 lines
docker logs --tail 50 log-aggregator

# Filter for duplicates
docker logs log-aggregator | Select-String "Duplicate"

# Filter for processed events
docker logs log-aggregator | Select-String "processed successfully"
```

## Cleanup

```powershell
# Stop and remove containers
docker-compose down

# Remove data folder (careful!)
Remove-Item -Recurse -Force data

# Remove Docker images
docker rmi log-aggregator:latest
```

## Troubleshooting

### Check if service is running
```powershell
docker ps | Select-String "log-aggregator"
```

### Check port availability
```powershell
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
```

### Test connectivity
```powershell
Test-NetConnection -ComputerName localhost -Port 8080
```

### View Docker Compose status
```powershell
docker-compose ps
```

---

**Note**: Pastikan Docker Desktop sudah berjalan di Windows sebelum menjalankan commands di atas.
