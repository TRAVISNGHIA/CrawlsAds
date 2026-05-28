from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from core.logger import get_logger
from database.models import CrawlStartRequest
from database.mongo import get_db
from services.crawler_service import (
    start_crawl_job,
)

router = APIRouter()

logger = get_logger(__name__)

class SchedulerConfig(BaseModel):

    enabled: bool = True

    times_per_day: int = 4

    devices: List[str] = ["desktop"]

    profiles: List[str] = []


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

        query["keyword"] = {
            "$regex": search,
            "$options": "i",
        }

    skip = (page - 1) * limit

    total = await db.keywords.count_documents(
        query
    )

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

        if (
            "created_at" in doc
            and isinstance(
                doc["created_at"],
                datetime,
            )
        ):
            doc["created_at"] = (
                doc["created_at"].isoformat()
            )

        if (
            "last_crawled_at" in doc
            and isinstance(
                doc["last_crawled_at"],
                datetime,
            )
        ):
            doc["last_crawled_at"] = (
                doc["last_crawled_at"].isoformat()
            )

        items.append(doc)

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/keywords")
async def add_keywords(
    body: KeywordCreateRequest,
):

    db = get_db()

    now = datetime.now(timezone.utc)

    keywords = [
        kw.strip()
        for kw in body.keywords
        if kw.strip()
    ]

    if not keywords:

        raise HTTPException(
            status_code=400,
            detail="No valid keywords provided",
        )

    from pymongo import UpdateOne

    operations = []

    for kw in keywords:

        operations.append(

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
        )

    result = await db.keywords.bulk_write(
        operations
    )

    inserted = result.upserted_count

    skipped = len(keywords) - inserted

    return {
        "status": "success",
        "inserted": inserted,
        "skipped": skipped,
        "message": (
            f"Thêm {inserted} keyword mới, "
            f"bỏ qua {skipped} trùng lặp"
        ),
    }


@router.put("/keywords/{keyword_id}")
async def update_keyword(
    keyword_id: str,
    body: KeywordUpdateRequest,
):

    db = get_db()

    try:

        oid = ObjectId(keyword_id)

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid keyword ID",
        )

    new_keyword = body.keyword.strip()

    if not new_keyword:

        raise HTTPException(
            status_code=400,
            detail="Keyword cannot be empty",
        )

    existing = await db.keywords.find_one(
        {
            "keyword": new_keyword,
            "_id": {"$ne": oid},
        }
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Keyword already exists",
        )

    result = await db.keywords.update_one(
        {"_id": oid},
        {
            "$set": {
                "keyword": new_keyword,
            }
        },
    )

    if result.matched_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Keyword not found",
        )

    return {
        "status": "success",
        "keyword": new_keyword,
    }


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
):

    db = get_db()

    try:

        oid = ObjectId(keyword_id)

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid keyword ID",
        )

    result = await db.keywords.delete_one(
        {"_id": oid}
    )

    if result.deleted_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Keyword not found",
        )

    return {
        "status": "success",
        "deleted": keyword_id,
    }

@router.post("/crawl")
@router.post("/crawl/start")
async def start_crawl(request: Request):
    body_bytes = await request.body()
    logger.error(f"RAW BODY: {body_bytes.decode()}")  # ← xem frontend gửi gì

    try:
        data = await request.json()
        crawl_request = CrawlStartRequest.model_validate(data)
    except Exception as e:
        logger.error(f"Validation error: {e}")
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

    config = await db.scheduler_config.find_one(
        {}
    )

    if config:

        config.pop("_id", None)

        return config

    return SchedulerConfig().model_dump()


@router.post("/crawl/auto/config")
async def update_scheduler_config(
    config: SchedulerConfig,
):

    db = get_db()

    await db.scheduler_config.update_one(
        {},
        {
            "$set": config.model_dump(),
        },
        upsert=True,
    )

    logger.info(
        f"⚙️ Scheduler config updated | "
        f"enabled={config.enabled} | "
        f"times_per_day={config.times_per_day} | "
        f"devices={config.devices} | "
        f"profiles={config.profiles}"
    )

    return {
        "status": "success",
        "message": "Scheduler config updated",
        "config": config.model_dump(),
    }

@router.get("/crawl/status/{run_id}")
async def crawl_status(
    run_id: str,
):

    db = get_db()

    run = await db.crawl_runs.find_one(
        {"run_id": run_id}
    )

    if not run:

        raise HTTPException(
            status_code=404,
            detail="Run ID not found",
        )

    run["_id"] = str(run["_id"])

    return run

