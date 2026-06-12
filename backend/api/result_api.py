from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from bson import ObjectId
from database.mongo import get_db
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _serialize(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/results")
async def get_results(
    keyword: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    has_ads: Optional[bool] = Query(None),
    location_uule: Optional[str] = Query(None),
    location_name: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    skip: int = Query(0, ge=0),
):
    db = get_db()
    query = {}

    if keyword:
        query["keyword"] = {"$regex": keyword, "$options": "i"}
    if device:
        query["device"] = device
    if domain:
        query["final_domain"] = {"$regex": domain, "$options": "i"}
    if run_id:
        query["run_id"] = run_id
    if has_ads is not None:
        query["has_ads"] = has_ads
    if location_uule:
        query["location_uule"] = location_uule
    if location_name:
        query["location_name"] = {"$regex": location_name, "$options": "i"}

    cursor = db.ad_results.find(query).sort("created_at", -1).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    total = await db.ad_results.count_documents(query)

    return {
        "results": [_serialize(r) for r in results],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.get("/results/{result_id}")
async def get_result(result_id: str):
    db = get_db()
    try:
        oid = ObjectId(result_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid result ID")

    result = await db.ad_results.find_one({"_id": oid})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return _serialize(result)


@router.delete("/results")
async def clear_results(run_id: Optional[str] = Query(None)):
    db = get_db()
    query = {"run_id": run_id} if run_id else {}
    deleted = await db.ad_results.delete_many(query)
    if not run_id:
        await db.crawl_runs.delete_many({})
    return {"deleted": deleted.deleted_count, "message": "Results cleared"}


@router.get("/stats")
async def get_stats():
    db = get_db()
    total_runs = await db.crawl_runs.count_documents({})
    total_results = await db.ad_results.count_documents({})
    total_ads = await db.ad_results.count_documents({"has_ads": True})
    total_keywords = await db.ad_results.distinct("keyword")

    latest_run = await db.crawl_runs.find_one(
        {}, {"_id": 0}, sort=[("started_at", -1)]
    )

    return {
        "total_runs": total_runs,
        "total_results": total_results,
        "total_ads_found": total_ads,
        "total_unique_keywords": len(total_keywords),
        "latest_run": latest_run,
    }