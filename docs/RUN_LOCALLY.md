# Menjalankan Log Aggregator secara Lokal (Tanpa Docker)

## 🚀 Quick Start

### Prerequisites
- Python 3.11 atau lebih baru
- pip (Python package manager)

### Langkah 1: Install Dependencies

```powershell
# PowerShell
cd "c:\Code\Dockerfile\UTS Sister"
pip install -r requirements.txt
```

```bash
# Linux/Mac
cd /path/to/project
pip install -r requirements.txt
```

### Langkah 2: Buat Data Directory

```powershell
# PowerShell
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" }
```

```bash
# Linux/Mac
mkdir -p data
```

### Langkah 3: Jalankan Aplikasi

Ada 3 cara untuk menjalankan aplikasi:

#### Cara 1: Run Langsung (Recommended)
```powershell
python src/main.py
```

#### Cara 2: Run sebagai Module
```powershell
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

#### Cara 3: Run dengan Reload (Development Mode)
```powershell
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

## ✅ Verifikasi

### 1. Check Health
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get | ConvertTo-Json
```

Expected Output:
```json
{
    "status": "healthy",
    "consumer_running": true,
    "queue_size": 0
}
```

### 2. Send Test Event
```powershell
$body = @{
    topic = "test.local"
    event_id = "evt-001"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "local-test"
    payload = @{ test = $true }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/publish" -Method Post -ContentType "application/json" -Body $body
```

### 3. Check Stats
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/stats" -Method Get | ConvertTo-Json
```

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Install dependencies
```powershell
pip install -r requirements.txt
```

### Error: "No such file or directory: 'data/dedup.db'"
**Solution:** Create data directory
```powershell
mkdir data
```

### Error: Port 8080 already in use
**Solution:** Use different port
```powershell
python -m uvicorn src.main:app --host 0.0.0.0 --port 8081
```

### Error: "ModuleNotFoundError: No module named 'src'"
**Solution:** This is fixed! The code now handles both:
- Direct execution: `python src/main.py`
- Module execution: `python -m uvicorn src.main:app`

## 🔧 Configuration

### Change Port
```powershell
# Edit command
python -m uvicorn src.main:app --host 0.0.0.0 --port 8081
```

### Change Log Level
```powershell
# Set environment variable
$env:LOG_LEVEL="DEBUG"
python src/main.py
```

### Change Database Path
Edit `src/main.py`:
```python
dedup_store = DedupStore(db_path="custom/path/dedup.db")
```

## 📊 Testing

### Run Test Publisher
```powershell
python test_publisher.py
```

Make sure to change the URL in test_publisher.py if using different port:
```python
AGGREGATOR_URL = "http://localhost:8081"  # Change if needed
```

## 🎯 Development Tips

### Auto-reload on Changes
```powershell
python -m uvicorn src.main:app --reload
```

### Debug Mode
```powershell
python -m uvicorn src.main:app --log-level debug
```

### Access API Documentation
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🛑 Stop Application

Press `Ctrl+C` in the terminal where the application is running.

## 📝 Notes

- SQLite database will be created in `data/dedup.db`
- Database persists between runs
- All processed events are stored in SQLite
- To reset database: delete `data/dedup.db` file

---

**Happy Coding! 🚀**
