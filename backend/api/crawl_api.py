from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import ValidationError, BaseModel
from typing import Optional, List
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bson import ObjectId

from database.mongo import get_db
from database.models import CrawlStartRequest
from services.crawler_service import start_crawl_job, start_auto_crawl_from_db
from core.logger import get_logger

crawl_lock = asyncio.Lock()
router = APIRouter()
logger = get_logger(__name__)

# Global scheduler
scheduler = AsyncIOScheduler()
scheduler_started = False


class SchedulerConfig(BaseModel):
    enabled: bool = True
    interval_hours: int = 6
    limit_keywords: int = 30
    devices: List[str]
    profiles: List[str]

class KeywordCreateRequest(BaseModel):
    keywords: List[str]


class KeywordUpdateRequest(BaseModel):
    keyword: str


@router.get("/keywords")
async def list_keywords(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query("", alias="search"),
):
    db = get_db()
    query = {}
    if search:
        query["keyword"] = {"$regex": search, "$options": "i"}

    skip = (page - 1) * limit
    total = await db.keywords.count_documents(query)
    cursor = db.keywords.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc and isinstance(doc["created_at"], datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if "last_crawled_at" in doc and isinstance(doc["last_crawled_at"], datetime):
            doc["last_crawled_at"] = doc["last_crawled_at"].isoformat()
        items.append(doc)

    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/keywords")
async def add_keywords(body: KeywordCreateRequest):
    db = get_db()
    now = datetime.now(timezone.utc)

    keywords = [kw.strip() for kw in body.keywords if kw.strip()]
    if not keywords:
        raise HTTPException(status_code=400, detail="No valid keywords provided")

    ops = []
    for kw in keywords:
        ops.append({
            "filter": {"keyword": kw},
            "update": {
                "$setOnInsert": {
                    "keyword": kw,
                    "created_at": now,
                    "last_crawled_at": None,
                    "crawl_count": 0,
                }
            },
            "upsert": True,
        })

    from pymongo import UpdateOne
    result = await db.keywords.bulk_write(
        [UpdateOne(op["filter"], op["update"], upsert=op["upsert"]) for op in ops]
    )

    inserted = result.upserted_count
    skipped = len(keywords) - inserted
    return {
        "status": "success",
        "inserted": inserted,
        "skipped": skipped,
        "message": f"Thêm {inserted} keyword mới, bỏ qua {skipped} trùng lặp",
    }


@router.put("/keywords/{keyword_id}")
async def update_keyword(keyword_id: str, body: KeywordUpdateRequest):
    db = get_db()
    try:
        oid = ObjectId(keyword_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid keyword ID")

    new_kw = body.keyword.strip()
    if not new_kw:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    existing = await db.keywords.find_one({"keyword": new_kw, "_id": {"$ne": oid}})
    if existing:
        raise HTTPException(status_code=409, detail="Keyword đã tồn tại")

    result = await db.keywords.update_one(
        {"_id": oid},
        {"$set": {"keyword": new_kw}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return {"status": "success", "keyword": new_kw}


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: str):
    db = get_db()
    try:
        oid = ObjectId(keyword_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid keyword ID")

    result = await db.keywords.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return {"status": "success", "deleted": keyword_id}


async def scheduled_crawl_task():
    # Nếu đang crawl thì bỏ qua
    if crawl_lock.locked():
        logger.warning("⚠️ Scheduler đang chạy job khác, bỏ qua lần này")
        return

    async with crawl_lock:
        logger.info("⏰ Scheduler: Bắt đầu crawl tự động từ database...")

        try:
            db = get_db()

            config_doc = await db.scheduler_config.find_one(
                {"name": "default"}
            )

            config = (
                SchedulerConfig(**config_doc)
                if config_doc
                else SchedulerConfig()
            )

            if not config.enabled:
                logger.info("⏸ Scheduler đang tắt")
                return

            logger.info(
                f"⚙️ Config: "
                f"limit={config.limit_keywords}, "
                f"devices={config.devices}, "
                f"profiles={config.profiles}"
            )

            run_id = await start_auto_crawl_from_db(
                limit=config.limit_keywords,
                devices=config.devices,
                profiles=config.profiles,
            )

            if run_id:
                logger.info(f"✅ Scheduler hoàn thành: {run_id}")

        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")


def start_scheduler(config: SchedulerConfig = None):
    global scheduler_started
    if scheduler_started:
        return

    if config is None:
        config = SchedulerConfig()

    if not config.enabled:
        logger.info("Scheduler đang tắt theo config")
        return

    try:
        scheduler.add_job(
            scheduled_crawl_task,
            IntervalTrigger(hours=config.interval_hours),
            id="auto_crawl_job",
            replace_existing=True,
            next_run_time=datetime.now(timezone.utc)
        )
        scheduler.start()
        scheduler_started = True
        logger.info(f"✅ Scheduler đã khởi động - Chạy mỗi {config.interval_hours} giờ")
    except Exception as e:
        logger.error(f"Không thể khởi động scheduler: {e}")


@router.post("/crawl")
@router.post("/crawl/start")
async def start_crawl(request: Request):
    try:
        body_bytes = await request.body()
        if not body_bytes:
            raise HTTPException(status_code=400, detail="Request body is empty")

        data = await request.json()
        crawl_request = CrawlStartRequest.model_validate(data)

        keywords = [kw.strip() for kw in crawl_request.keywords if kw.strip()]
        if not keywords:
            raise HTTPException(status_code=400, detail="No valid keywords provided")

        crawl_request.keywords = keywords
        run_id = await start_crawl_job(crawl_request)

        return {
            "run_id": run_id,
            "status": "pending",
            "message": f"Crawl started for {len(keywords)} keyword(s)",
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


@router.post("/crawl/auto/config")
async def update_scheduler_config(config: SchedulerConfig):
    db = get_db()

    await db.scheduler_config.update_one(
        {"name": "default"},
        {"$set": {"name": "default", **config.model_dump()}},
        upsert=True
    )

    global scheduler_started
    if scheduler.running:
        scheduler.remove_all_jobs()
        if config.enabled:
            scheduler.add_job(
                scheduled_crawl_task,
                IntervalTrigger(hours=config.interval_hours),
                id="auto_crawl_job",
                replace_existing=True,
            )
            logger.info(f"🔄 Scheduler đã cập nhật: mỗi {config.interval_hours} giờ, {config.limit_keywords} keywords")
        else:
            logger.info("⏸ Scheduler đã tắt theo yêu cầu")
    elif config.enabled:
        scheduler_started = False
        start_scheduler(config)

    return {
        "status": "success",
        "message": f"Đã lưu: chạy mỗi {config.interval_hours} giờ, {config.limit_keywords} keywords, devices={config.devices}",
        "config": config.model_dump(),
    }


@router.get("/crawl/auto/config")
async def get_scheduler_config():
    db = get_db()
    config = await db.scheduler_config.find_one({"name": "default"})
    if config:
        config.pop("_id", None)
        return config
    return SchedulerConfig().model_dump()


@router.post("/crawl/auto/start")
async def manual_start_scheduler():
    start_scheduler()
    return {"status": "success", "message": "Scheduler đã được khởi động"}


@router.post("/crawl/auto/stop")
async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        global scheduler_started
        scheduler_started = False
        return {"status": "success", "message": "Scheduler đã dừng"}
    return {"status": "info", "message": "Scheduler chưa chạy"}


@router.get("/crawl/status/{run_id}")
async def crawl_status(run_id: str):
    db = get_db()
    run = await db.crawl_runs.find_one({"run_id": run_id})
    if not run:
        raise HTTPException(status_code=404, detail="Run ID not found")
    if "_id" in run:
        run["_id"] = str(run["_id"])
    return run


@router.on_event("startup")
async def startup_event():
    db = get_db()
    config_doc = await db.scheduler_config.find_one({"name": "default"})

    if config_doc:
        config = SchedulerConfig(**config_doc)
    else:
        config = SchedulerConfig()

    start_scheduler(config)