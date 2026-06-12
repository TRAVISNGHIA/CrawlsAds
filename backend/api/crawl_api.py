from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from core.logger import get_logger
from database.models import CrawlStartRequest, LocationCreateRequest, LocationUpdateRequest
from database.mongo import get_db
from services.crawler_service import start_crawl_job

router = APIRouter()
logger = get_logger(__name__)

class SchedulerConfig(BaseModel):
    enabled: bool = True
    times_per_day: int = 4
    devices: List[str] = ["desktop"]
    profiles: List[str] = []
    locations: List[str] = []


class KeywordCreateRequest(BaseModel):
    keywords: List[str]


class KeywordUpdateRequest(BaseModel):
    keyword: str

@router.get("/locations")
async def list_locations():
    db = get_db()
    cursor = db.locations.find({}).sort("name", 1)
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return {"items": items, "total": len(items)}


@router.post("/locations")
async def add_location(body: LocationCreateRequest):
    db = get_db()

    uule = body.uule.strip()
    name = body.name.strip()

    if not uule or not name:
        raise HTTPException(status_code=400, detail="uule và name không được để trống")

    existing = await db.locations.find_one({"uule": uule})
    if existing:
        raise HTTPException(status_code=409, detail="Location với uule này đã tồn tại")

    now = datetime.now(timezone.utc)
    doc = {
        "uule": uule,
        "name": name,
        "created_at": now,
    }
    result = await db.locations.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["created_at"] = now.isoformat()

    return {"status": "success", "location": doc}


@router.put("/locations/{location_id}")
async def update_location(location_id: str, body: LocationUpdateRequest):
    db = get_db()

    try:
        oid = ObjectId(location_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    update_data = {}
    if body.uule is not None:
        uule = body.uule.strip()
        if not uule:
            raise HTTPException(status_code=400, detail="uule không được để trống")
        # kiểm tra trùng uule với document khác
        conflict = await db.locations.find_one({"uule": uule, "_id": {"$ne": oid}})
        if conflict:
            raise HTTPException(status_code=409, detail="uule này đã được dùng bởi location khác")
        update_data["uule"] = uule

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="name không được để trống")
        update_data["name"] = name

    if not update_data:
        raise HTTPException(status_code=400, detail="Không có field nào để cập nhật")

    result = await db.locations.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")

    return {"status": "success", "updated": update_data}


@router.delete("/locations/{location_id}")
async def delete_location(location_id: str):
    db = get_db()

    try:
        oid = ObjectId(location_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    result = await db.locations.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")

    return {"status": "success", "deleted": location_id}

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

    cursor = (
        db.keywords
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

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

    from pymongo import UpdateOne
    operations = [
        UpdateOne(
            {"keyword": kw},
            {
                "$setOnInsert": {
                    "keyword": kw,
                    "enabled": True,
                    "created_at": now,
                    "last_crawled_at": None,
                    "crawl_count": 0,
                }
            },
            upsert=True,
        )
        for kw in keywords
    ]

    result = await db.keywords.bulk_write(operations)
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

    new_keyword = body.keyword.strip()
    if not new_keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")

    existing = await db.keywords.find_one({"keyword": new_keyword, "_id": {"$ne": oid}})
    if existing:
        raise HTTPException(status_code=409, detail="Keyword already exists")

    result = await db.keywords.update_one({"_id": oid}, {"$set": {"keyword": new_keyword}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return {"status": "success", "keyword": new_keyword}


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


@router.patch("/keywords/{keyword_id}/toggle")
async def toggle_keyword(keyword_id: str):
    db = get_db()

    try:
        oid = ObjectId(keyword_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid keyword ID")

    kw = await db.keywords.find_one({"_id": oid})
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")

    new_enabled = not kw.get("enabled", True)
    await db.keywords.update_one({"_id": oid}, {"$set": {"enabled": new_enabled}})

    return {"status": "success", "enabled": new_enabled}

@router.post("/crawl")
@router.post("/crawl/start")
async def start_crawl(request: Request):
    body_bytes = await request.body()
    if not body_bytes or not body_bytes.strip():
        return {"status": "ignored", "message": "Empty body"}

    try:
        data = await request.json()
        crawl_request = CrawlStartRequest.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

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
@router.get("/crawl/auto/config")
async def get_scheduler_config():
    db = get_db()
    config = await db.scheduler_config.find_one({})
    if config:
        config.pop("_id", None)
        if "runs_per_day" in config and "times_per_day" not in config:
            config["times_per_day"] = config.pop("runs_per_day")
        return config
    return SchedulerConfig().model_dump()


@router.post("/crawl/auto/config")
async def update_scheduler_config(config: SchedulerConfig):
    db = get_db()

    await db.scheduler_config.update_one(
        {},
        {"$set": config.model_dump()},
        upsert=True,
    )

    logger.info(
        f"⚙️ Scheduler config updated | "
        f"enabled={config.enabled} | "
        f"times_per_day={config.times_per_day} | "
        f"devices={config.devices} | "
        f"profiles={config.profiles} | "
        f"locations={config.locations}"
    )

    return {
        "status": "success",
        "message": "Scheduler config updated",
        "config": config.model_dump(),
    }

@router.get("/crawl/status/{run_id}")
async def crawl_status(run_id: str):
    db = get_db()
    run = await db.crawl_runs.find_one({"run_id": run_id})

    if not run:
        raise HTTPException(status_code=404, detail="Run ID not found")

    run["_id"] = str(run["_id"])
    return run