from fastapi import APIRouter, HTTPException
from database.models import CrawlStartRequest
from database.mongo import get_db
from services.crawler_service import start_crawl_job
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/crawl")
@router.post("/crawl/start")
async def start_crawl(request: CrawlStartRequest):
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
    if not request.devices:
        raise HTTPException(status_code=400, detail="At least one device is required")

    # Sanitize keywords
    keywords = [kw.strip() for kw in request.keywords if kw.strip()]
    if not keywords:
        raise HTTPException(status_code=400, detail="No valid keywords provided")

    request.keywords = keywords
    run_id = await start_crawl_job(request)

    return {
        "run_id": run_id,
        "status": "pending",
        "message": f"Crawl started for {len(keywords)} keyword(s)",
        "keywords": keywords,
        "devices": request.devices,
        "profiles": request.profiles,
    }


@router.get("/crawl/status/{run_id}")
async def get_crawl_status(run_id: str):
    db = get_db()
    run = await db.crawl_runs.find_one({"run_id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    # Calculate progress percentage
    total = run.get("total_keywords", 0)
    processed = run.get("processed_keywords", 0)
    progress = round((processed / total * 100) if total > 0 else 0, 1)

    return {**run, "progress": progress}


@router.get("/crawl/runs")
async def list_runs(limit: int = 20):
    db = get_db()
    cursor = db.crawl_runs.find({}, {"_id": 0}).sort("started_at", -1).limit(limit)
    runs = await cursor.to_list(length=limit)
    return {"runs": runs, "count": len(runs)}
