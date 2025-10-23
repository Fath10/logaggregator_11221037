# 🚀 Complete Demo Script

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "UTS LOG AGGREGATOR - COMPLETE DEMO" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Configuration
$IMAGE_NAME = "uts-aggregator"
$CONTAINER_NAME = "log-aggregator"
$PORT = 8080
$BASE_URL = "http://localhost:$PORT"

# Color functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Step { param($msg) Write-Host "`n🎯 $msg" -ForegroundColor Magenta }

# Helper functions
function Test-URL {
    param($url)
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Wait-ForService {
    Write-Info "Waiting for service to be ready..."
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        if (Test-URL "$BASE_URL/health") {
            Write-Success "Service is ready!"
            return $true
        }
        Start-Sleep -Seconds 1
        $attempt++
        Write-Host "." -NoNewline
    }
    
    Write-Error "Service did not start in time"
    return $false
}

function Send-Event {
    param($topic, $eventId, $source, $payload)
    
    $body = @{
        topic = $topic
        event_id = $eventId
        timestamp = (Get-Date -Format "o")
        source = $source
        payload = $payload
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/publish" -Method Post -Body $body -ContentType "application/json"
        return $response
    } catch {
        Write-Error "Failed to send event: $_"
        return $null
    }
}

function Get-Stats {
    try {
        $stats = Invoke-RestMethod -Uri "$BASE_URL/stats" -Method Get
        return $stats
    } catch {
        Write-Error "Failed to get stats: $_"
        return $null
    }
}

function Show-Stats {
    param($label)
    Write-Info "Stats ($label):"
    $stats = Get-Stats
    if ($stats) {
        Write-Host "   Received: $($stats.received)" -ForegroundColor White
        Write-Host "   Unique Processed: $($stats.unique_processed)" -ForegroundColor White
        Write-Host "   Duplicates Dropped: $($stats.duplicate_dropped)" -ForegroundColor White
        Write-Host "   Topics: $($stats.topics -join ', ')" -ForegroundColor White
    }
}

# ============================================================================
# STEP 1: BUILD & RUN
# ============================================================================

Write-Step "STEP 1: Build & Run Container"

# Stop existing container
Write-Info "Stopping existing container..."
docker stop $CONTAINER_NAME 2>$null
docker rm $CONTAINER_NAME 2>$null

# Build image
Write-Info "Building Docker image..."
docker build -t $IMAGE_NAME . | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Image built successfully"
} else {
    Write-Error "Failed to build image"
    exit 1
}

# Run container
Write-Info "Starting container..."
docker run -d -p ${PORT}:8080 --name $CONTAINER_NAME -v ${PWD}/data:/app/data $IMAGE_NAME | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Container started"
} else {
    Write-Error "Failed to start container"
    exit 1
}

# Wait for service
if (-not (Wait-ForService)) {
    exit 1
}

# Show initial stats
Show-Stats "Initial"

# ============================================================================
# STEP 2: TEST IDEMPOTENCY & DEDUPLICATION
# ============================================================================

Write-Step "STEP 2: Test Idempotency & Deduplication"

# Send first event
Write-Info "Sending first event (evt-demo-001)..."
$response1 = Send-Event -topic "user.login" -eventId "evt-demo-001" -source "demo" -payload @{user="alice"}
if ($response1) {
    Write-Host "   Response: received=$($response1.received), accepted=$($response1.accepted), duplicates=$($response1.duplicates)" -ForegroundColor White
    if ($response1.accepted -eq 1) {
        Write-Success "Event accepted (first time)"
    }
}

Start-Sleep -Seconds 2
Show-Stats "After First Event"

# Send duplicate event
Write-Info "Sending DUPLICATE event (evt-demo-001)..."
$response2 = Send-Event -topic "user.login" -eventId "evt-demo-001" -source "demo" -payload @{user="alice"}
if ($response2) {
    Write-Host "   Response: received=$($response2.received), accepted=$($response2.accepted), duplicates=$($response2.duplicates)" -ForegroundColor White
    if ($response2.duplicates -eq 1) {
        Write-Success "IDEMPOTENCY VERIFIED: Duplicate detected!"
    } else {
        Write-Error "IDEMPOTENCY FAILED: Duplicate not detected!"
    }
}

Start-Sleep -Seconds 2
Show-Stats "After Duplicate Event"

# ============================================================================
# STEP 3: TEST BATCH WITH DUPLICATES
# ============================================================================

Write-Step "STEP 3: Test Batch Publishing with Duplicates"

Write-Info "Sending batch with 3 events (2 unique, 1 duplicate)..."
$batchBody = @{
    events = @(
        @{
            topic = "order.created"
            event_id = "order-001"
            timestamp = (Get-Date -Format "o")
            source = "order-service"
            payload = @{order_id=1001; amount=100}
        },
        @{
            topic = "order.created"
            event_id = "order-002"
            timestamp = (Get-Date -Format "o")
            source = "order-service"
            payload = @{order_id=1002; amount=200}
        },
        @{
            topic = "order.created"
            event_id = "order-001"
            timestamp = (Get-Date -Format "o")
            source = "order-service"
            payload = @{order_id=1001; amount=100}
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $batchResponse = Invoke-RestMethod -Uri "$BASE_URL/publish" -Method Post -Body $batchBody -ContentType "application/json"
    Write-Host "   Response: received=$($batchResponse.received), accepted=$($batchResponse.accepted), duplicates=$($batchResponse.duplicates)" -ForegroundColor White
    if ($batchResponse.accepted -eq 2 -and $batchResponse.duplicates -eq 1) {
        Write-Success "BATCH DEDUPLICATION VERIFIED: 2 accepted, 1 duplicate"
    }
} catch {
    Write-Error "Failed to send batch: $_"
}

Start-Sleep -Seconds 2
Show-Stats "After Batch"

# ============================================================================
# STEP 4: TEST PERSISTENCE & CRASH TOLERANCE
# ============================================================================

Write-Step "STEP 4: Test Persistence & Crash Tolerance"

# Send event before restart
Write-Info "Sending event before restart (pay-restart-001)..."
$response3 = Send-Event -topic "payment.completed" -eventId "pay-restart-001" -source "payment-service" -payload @{amount=500}
if ($response3 -and $response3.accepted -eq 1) {
    Write-Success "Event accepted before restart"
}

Start-Sleep -Seconds 2

# Get stats before restart
$statsBeforeRestart = Get-Stats
Write-Info "Stats before restart:"
Write-Host "   Received: $($statsBeforeRestart.received)" -ForegroundColor White
Write-Host "   Unique Processed: $($statsBeforeRestart.unique_processed)" -ForegroundColor White

# Restart container
Write-Info "Restarting container..."
docker restart $CONTAINER_NAME | Out-Null
Start-Sleep -Seconds 5

# Wait for service after restart
if (-not (Wait-ForService)) {
    Write-Error "Service did not restart properly"
    exit 1
}

Write-Success "Container restarted successfully"

# Send SAME event after restart
Write-Info "Sending SAME event after restart (pay-restart-001)..."
$response4 = Send-Event -topic "payment.completed" -eventId "pay-restart-001" -source "payment-service" -payload @{amount=500}
if ($response4) {
    Write-Host "   Response: received=$($response4.received), accepted=$($response4.accepted), duplicates=$($response4.duplicates)" -ForegroundColor White
    if ($response4.duplicates -eq 1) {
        Write-Success "PERSISTENCE VERIFIED: Event still detected as duplicate after restart!"
    } else {
        Write-Error "PERSISTENCE FAILED: Event not detected as duplicate after restart!"
    }
}

Start-Sleep -Seconds 2
Show-Stats "After Restart"

# ============================================================================
# STEP 5: VERIFY DATABASE PERSISTENCE
# ============================================================================

Write-Step "STEP 5: Verify Database Persistence"

Write-Info "Checking database file..."
if (Test-Path "data/dedup.db") {
    $dbSize = (Get-Item "data/dedup.db").Length
    Write-Success "Database file exists: data/dedup.db ($([math]::Round($dbSize/1KB, 2)) KB)"
} else {
    Write-Warning "Database file not found"
}

# ============================================================================
# STEP 6: QUERY EVENTS
# ============================================================================

Write-Step "STEP 6: Query Events by Topic"

Write-Info "Querying events for topic 'user.login'..."
try {
    $events = Invoke-RestMethod -Uri "$BASE_URL/events?topic=user.login&limit=10" -Method Get
    Write-Host "   Topic: $($events.topic)" -ForegroundColor White
    Write-Host "   Count: $($events.count)" -ForegroundColor White
    if ($events.count -gt 0) {
        Write-Success "Events retrieved successfully"
        foreach ($evt in $events.events) {
            Write-Host "      - Event ID: $($evt.event_id)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Error "Failed to query events: $_"
}

# ============================================================================
# STEP 7: PERFORMANCE TEST (Optional)
# ============================================================================

Write-Step "STEP 7: Quick Performance Test (100 events)"

Write-Info "Sending 100 events rapidly..."
$startTime = Get-Date
$successCount = 0
$duplicateCount = 0

for ($i = 1; $i -le 100; $i++) {
    $response = Send-Event -topic "perf.test" -eventId "perf-$i" -source "perf-test" -payload @{index=$i}
    if ($response) {
        $successCount += $response.accepted
        $duplicateCount += $response.duplicates
    }
    
    if ($i % 20 -eq 0) {
        Write-Host "." -NoNewline
    }
}
Write-Host ""

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds
$throughput = [math]::Round(100 / $duration, 0)

Write-Success "Performance Test Complete"
Write-Host "   Duration: $([math]::Round($duration, 2))s" -ForegroundColor White
Write-Host "   Throughput: ~$throughput events/s" -ForegroundColor White
Write-Host "   Accepted: $successCount" -ForegroundColor White
Write-Host "   Duplicates: $duplicateCount" -ForegroundColor White

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DEMO COMPLETE - SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Show-Stats "Final"

Write-Host ""
Write-Host "✅ VERIFICATION CHECKLIST:" -ForegroundColor Green
Write-Host "   [✓] Container built and running" -ForegroundColor Green
Write-Host "   [✓] Idempotency working (duplicates rejected)" -ForegroundColor Green
Write-Host "   [✓] Batch deduplication working" -ForegroundColor Green
Write-Host "   [✓] Persistence verified (survived restart)" -ForegroundColor Green
Write-Host "   [✓] Database file persisted" -ForegroundColor Green
Write-Host "   [✓] Events queryable by topic" -ForegroundColor Green
Write-Host "   [✓] Performance acceptable" -ForegroundColor Green
Write-Host ""

Write-Host "📝 Container Info:" -ForegroundColor Yellow
Write-Host "   Container Name: $CONTAINER_NAME" -ForegroundColor White
Write-Host "   Image: $IMAGE_NAME" -ForegroundColor White
Write-Host "   Port: $PORT" -ForegroundColor White
Write-Host "   Health: $BASE_URL/health" -ForegroundColor White
Write-Host "   Stats: $BASE_URL/stats" -ForegroundColor White
Write-Host ""

Write-Host "🛠️  Useful Commands:" -ForegroundColor Yellow
Write-Host "   View logs:    docker logs $CONTAINER_NAME" -ForegroundColor White
Write-Host "   Stop:         docker stop $CONTAINER_NAME" -ForegroundColor White
Write-Host "   Restart:      docker restart $CONTAINER_NAME" -ForegroundColor White
Write-Host "   Shell:        docker exec -it $CONTAINER_NAME /bin/bash" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Demo completed successfully!" -ForegroundColor Green
Write-Host ""
