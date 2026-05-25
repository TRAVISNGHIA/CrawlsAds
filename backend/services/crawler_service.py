import asyncio
import uuid
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from database.mongo import get_db
from database.models import CrawlRun, AdResult, CrawlStartRequest
from services.browser_factory import create_browser
from services.ad_extractor import search_and_extract_ads
from services.capture_service import capture_full_page_screenshot, save_html_snapshot
from utils.file_utils import get_screenshot_path, get_html_path, relative_storage_path
from core.logger import get_logger

logger = get_logger(__name__)


async def start_crawl_job(request: CrawlStartRequest) -> str:
    run_id = str(uuid.uuid4())
    db = get_db()

    keywords = request.keywords if isinstance(request.keywords, list) else [request.keywords]
    devices = request.devices if isinstance(request.devices, list) else [request.devices]
    profiles = request.profiles if isinstance(request.profiles, list) else [request.profiles]

    run = CrawlRun(
        run_id=run_id,
        status="pending",
        total_keywords=len(keywords) * len(devices) * len(profiles),
        processed_keywords=0,
        devices=devices,
        profiles=profiles,
        started_at=datetime.now(timezone.utc),
    )

    await db.crawl_runs.insert_one(run.model_dump())
    logger.info(f"Crawl job created: {run_id}")

    asyncio.create_task(_run_crawl_async(run_id, keywords, devices, profiles))
    return run_id


async def start_auto_crawl_from_db(
        limit: int = 50,
        devices: Optional[List[str]] = None,
        profiles: Optional[List[str]] = None
) -> Optional[str]:

    db = get_db()

    # Lấy keywords từ database
    cursor = db.keywords.find({}, {"keyword": 1, "_id": 0}).limit(limit)
    keyword_docs = await cursor.to_list(length=limit)

    keywords = [doc["keyword"].strip() for doc in keyword_docs if doc.get("keyword")]

    if not keywords:
        logger.warning("Không tìm thấy keyword nào trong collection 'keywords'")
        return None

    # Default values
    devices = devices or ["desktop"]
    profiles = profiles or ["Profile 44"]

    logger.info(f"🚀 Bắt đầu crawl tự động từ DB: {len(keywords)} keywords | devices={devices} | profiles={profiles}")

    # Tạo request
    request = CrawlStartRequest(
        keywords=keywords,
        devices=devices,
        profiles=profiles
    )

    run_id = await start_crawl_job(request)
    return run_id


async def _run_crawl_async(
        run_id: str,
        keywords: List[str],
        devices: List[str],
        profiles: List[str],
):
    db = get_db()
    loop = asyncio.get_running_loop()

    await db.crawl_runs.update_one(
        {"run_id": run_id},
        {"$set": {"status": "running", "error": None}},
    )

    processed = 0
    total = len(keywords) * len(devices) * len(profiles)

    try:
        for device in devices:
            for profile in profiles:
                driver = None
                with ThreadPoolExecutor(max_workers=1) as browser_executor:
                    try:
                        driver = await loop.run_in_executor(
                            browser_executor, create_browser, device, profile
                        )

                        for i, keyword in enumerate(keywords):
                            try:
                                docs = await loop.run_in_executor(
                                    browser_executor,
                                    _process_keyword_sync,
                                    driver, keyword, run_id, device, profile,
                                )
                                if docs:
                                    await db.ad_results.insert_many(docs)
                            except Exception as e:
                                logger.error(f"Keyword '{keyword}' failed | device={device}, profile={profile}: {e}")
                                await _save_error_result(db, run_id, keyword, device, profile, str(e))
                            finally:
                                processed += 1
                                await db.crawl_runs.update_one(
                                    {"run_id": run_id},
                                    {"$set": {"processed_keywords": processed}},
                                )

                            if i < len(keywords) - 1:
                                delay = random.uniform(4, 9)
                                await asyncio.sleep(delay)

                    except Exception as e:
                        logger.error(f"Browser failed | device={device}, profile={profile}: {e}")
                        for kw in keywords:
                            processed += 1
                            await _save_error_result(db, run_id, kw, device, profile, str(e))
                            await db.crawl_runs.update_one({"run_id": run_id},
                                                           {"$set": {"processed_keywords": processed}})
                    finally:
                        if driver:
                            await loop.run_in_executor(browser_executor, _safe_quit, driver)

        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {"$set": {"status": "completed", "processed_keywords": processed,
                      "finished_at": datetime.now(timezone.utc)}}
        )
        logger.info(f"Crawl {run_id} completed. {processed}/{total}")

    except Exception as e:
        logger.error(f"Crawl {run_id} failed: {e}")
        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {"$set": {"status": "failed", "finished_at": datetime.now(timezone.utc), "error": str(e)}}
        )

def _process_keyword_sync(
    driver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Any]]:

    ad_list = search_and_extract_ads(driver, keyword, run_id, device, profile_name)

    screenshot_path = get_screenshot_path(run_id, keyword, device)
    capture_full_page_screenshot(driver, screenshot_path)

    html_path = get_html_path(run_id, keyword, device)
    save_html_snapshot(driver, html_path)

    docs: List[Dict[str, Any]] = []

    if not ad_list:
        no_ads = AdResult(
            run_id=run_id,
            keyword=keyword,
            device=device,
            profile_name=profile_name,
            has_ads=False,
            screenshot_path=relative_storage_path(screenshot_path),
            html_path=relative_storage_path(html_path),
        )
        docs.append(no_ads.model_dump())
    else:
        for ad in ad_list:
            ad["screenshot_path"] = relative_storage_path(screenshot_path)
            ad["html_path"] = relative_storage_path(html_path)
            docs.append(AdResult(**ad).model_dump())

    logger.info(f"Processed '{keyword}' [{device}] — {len(ad_list)} ads")
    return docs


async def _save_error_result(db, run_id, keyword, device, profile_name, error_msg):
    result = AdResult(
        run_id=run_id,
        keyword=keyword,
        device=device,
        profile_name=profile_name,
        has_ads=False,
        advertiser=f"ERROR: {error_msg[:200]}",
    )
    await db.ad_results.insert_one(result.model_dump())


def _safe_quit(driver):
    try:
        driver.quit()
    except Exception:
        pass