# SEM Checker 🔍

An automated Google SEM (Search Engine Marketing) ad detection and monitoring tool. Crawls Google Search results for specified keywords, detects sponsored ads, extracts ad data, captures screenshots, and displays results on a React dashboard.

## Architecture

```
┌──────────────┐    HTTP/REST    ┌──────────────────┐    Selenium    ┌──────────────┐
│   React UI   │◄──────────────►│   FastAPI Backend │◄─────────────►│  Chrome CDP  │
│  (Vite/TS)   │                │  (Python 3.10+)   │               │  (Google.com)│
└──────────────┘                └────────┬─────────┘               └──────────────┘
                                         │
                                    ┌────▼─────┐
                                    │ MongoDB  │
                                    └──────────┘
```

## Features

- **Multi-keyword crawling** — check any number of keywords in one run
- **Multi-device simulation** — Desktop, Mobile (iPhone), Tablet (iPad) via Chrome DevTools Protocol
- **Chrome profile management** — use named Chrome profiles, auto-cleans lock files
- **Ad detection** — detects "Sponsored", "Ad", "Quảng cáo", "Được tài trợ" labels
- **URL resolution** — follows Google redirect links (`/aclk`, `/url`) to final advertiser URLs
- **Full-page screenshots** — saved locally and served via FastAPI static files
- **HTML snapshots** — full page source saved per keyword/device
- **MongoDB persistence** — crawl runs, statuses, and all ad results stored
- **Live status polling** — frontend polls crawl status every 2.5 seconds
- **Filterable results table** — filter by keyword, device, domain, has_ads

## Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB 6.0+ (local or remote)
- Google Chrome browser
- ChromeDriver matching your Chrome version (undetected-chromedriver handles this automatically)

## Backend Setup

```bash
cd sem-checker/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed (see Environment Variables below)
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `sem_checker` | Database name |
| `CHROME_BINARY` | *(auto)* | Path to Chrome binary, e.g. `/usr/bin/google-chrome` |
| `CHROME_PROFILE_ROOT` | *(empty)* | Root dir containing Chrome profiles to clone |
| `CHROME_PROFILE_CLONE_ROOT` | `/tmp/sem_checker_profiles` | Where cloned profiles are stored |
| `BACKEND_HOST` | `0.0.0.0` | FastAPI bind host |
| `BACKEND_PORT` | `8000` | FastAPI port |
| `FRONTEND_URL` | `http://localhost:5173` | CORS allowed origin |
| `CAPTURE_FULLPAGE` | `true` | Whether to capture full-page screenshots |

## Running the Backend

```bash
cd sem-checker/backend
source venv/bin/activate
python main.py
# Or with uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

## Frontend Setup

```bash
cd sem-checker/frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

## MongoDB Setup

### Local (Ubuntu/Debian)
```bash
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Docker
```bash
docker run -d --name mongo -p 27017:27017 mongo:6
```

## API Reference

### Health Check
```
GET /api/health
```

### Start Crawl
```
POST /api/crawl/start
Content-Type: application/json

{
  "keywords": ["buy laptop", "online loan"],
  "devices": ["desktop", "mobile"],
  "profiles": ["Default"],
}
```
Response:
```json
{
  "run_id": "uuid-here",
  "status": "pending",
  "message": "Crawl started for 2 keyword(s)"
}
```

### Get Crawl Status
```
GET /api/crawl/status/{run_id}
```

### List All Runs
```
GET /api/crawl/runs
```

### Get Results
```
GET /api/results?keyword=laptop&device=desktop&domain=example.com&has_ads=true
```

### Get Stats
```
GET /api/stats
```

### Delete Results
```
DELETE /api/results              # clear everything
DELETE /api/results?run_id=xxx   # clear specific run
```

## Storage

- Screenshots: `backend/storage/screenshots/`
- HTML snapshots: `backend/storage/html/`
- Served at: `http://localhost:8000/storage/screenshots/filename.png`

## Project Structure

```
sem-checker/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── crawl_api.py            # Crawl start/status endpoints
│   │   ├── result_api.py           # Results CRUD endpoints
│   │   └── health_api.py           # Health check
│   ├── core/
│   │   ├── config.py               # Pydantic settings
│   │   └── logger.py               # Logging setup
│   ├── database/
│   │   ├── mongo.py                # MongoDB connection
│   │   └── models.py               # Pydantic data models
│   ├── services/
│   │   ├── crawler_service.py      # Orchestrates crawl jobs
│   │   ├── browser_factory.py      # Creates Chrome instances
│   │   ├── profile_manager.py      # Chrome profile cloning
│   │   ├── ad_extractor.py         # Google ad detection & parsing
│   │   ├── url_resolver.py         # Follows redirects to final URLs
│   │   ├── capture_service.py      # Screenshots & HTML snapshots
│   │   └── device_emulation.py     # Device configs (desktop/mobile/tablet)
│   ├── storage/
│   │   ├── screenshots/
│   │   └── html/
│   └── utils/
│       └── file_utils.py
│
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── api/client.ts           # Typed API client
    │   ├── pages/
    │   │   ├── Dashboard.tsx       # Stats overview
    │   │   ├── CrawlPage.tsx       # Start & monitor crawls
    │   │   └── ResultsPage.tsx     # Browse & filter results
    │   └── components/
    │       ├── Layout.tsx
    │       ├── Navbar.tsx
    │       ├── ResultTable.tsx     # Sortable table with modals
    │       └── StatusBadge.tsx
```

## Troubleshooting

### Chrome/ChromeDriver Issues

**"Chrome not found" error**  
Set `CHROME_BINARY` in `.env` to your Chrome path:
- Linux: `/usr/bin/google-chrome` or `/usr/bin/chromium-browser`
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`

**ChromeDriver version mismatch**  
`undetected-chromedriver` downloads the correct ChromeDriver automatically. If it fails:
```bash
pip install --upgrade undetected-chromedriver
```

**Profile lock error**  
The system automatically cleans `SingletonLock`, `SingletonCookie`, and `SingletonSocket` files. If Chrome crashes without cleanup, manually delete:
```bash
rm -f /tmp/sem_checker_profiles/profile_Default/Singleton*
```

**Headless not working on Linux servers**  
Install Chrome dependencies:
```bash
sudo apt install -y xvfb libgconf-2-4 libnss3 libgbm1
```

### MongoDB Connection Failed
Ensure MongoDB is running:
```bash
sudo systemctl status mongod
# or
mongosh --eval "db.adminCommand('ping')"
```

### No Ads Detected
Google frequently changes its HTML structure. The extractor uses multiple strategies (label text + CSS selectors). If detection fails:
1. Run in non-headless mode to visually inspect the page
2. Check `backend/storage/html/` for the saved HTML snapshot
3. Update selectors in `services/ad_extractor.py` → `AD_CONTAINER_SELECTORS`

### CORS Error from Frontend
Ensure `FRONTEND_URL` in `.env` matches exactly where the frontend runs (default: `http://localhost:5173`).
