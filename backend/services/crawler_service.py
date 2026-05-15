import asyncio
import uuid
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor

from database.mongo import get_db
from database.models import CrawlRun, AdResult, CrawlStartRequest
from services.browser_factory import create_browser
from services.ad_extractor import search_and_extract_ads
from services.capture_service import (
    capture_full_page_screenshot,
    save_html_snapshot,
)
from utils.file_utils import get_screenshot_path, get_html_path, relative_storage_path
from core.logger import get_logger

logger = get_logger(__name__)
executor = ThreadPoolExecutor(max_workers=3)


async def start_crawl_job(request: CrawlStartRequest) -> str:
    run_id = str(uuid.uuid4())
    db = get_db()

    run = CrawlRun(
        run_id=run_id,
        status="pending",
        total_keywords=len(request.keywords) * len(request.devices) * len(request.profiles),
        processed_keywords=0,
        devices=request.devices,
        profiles=request.profiles,
        started_at=datetime.utcnow(),
    )

    await db.crawl_runs.insert_one(run.model_dump())
    logger.info(f"Crawl job created: {run_id}")

    # Run crawl in thread executor to avoid blocking event loop
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        executor,
        _run_crawl_sync,
        run_id,
        request.keywords,
        request.devices,
        request.profiles,
        request.headless,
    )

    return run_id


def _run_crawl_sync(
    run_id: str,
    keywords: List[str],
    devices: List[str],
    profiles: List[str],
    headless: bool,
):
    """Synchronous crawl execution — runs in thread pool."""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        _run_crawl_async(run_id, keywords, devices, profiles, headless)
    )
    loop.close()


async def _run_crawl_async(
    run_id: str,
    keywords: List[str],
    devices: List[str],
    profiles: List[str],
    headless: bool,
):
    """Core async crawl logic."""
    db = get_db()
    await db.crawl_runs.update_one(
        {"run_id": run_id}, {"$set": {"status": "running"}}
    )

    processed = 0
    total = len(keywords) * len(devices) * len(profiles)

    try:
        for device in devices:
            for profile in profiles:
                driver = None
                try:
                    driver = create_browser(device, profile, headless)
                    for keyword in keywords:
                        try:
                            await _process_keyword(
                                driver, keyword, run_id, device, profile
                            )
                        except Exception as e:
                            logger.error(f"Keyword '{keyword}' failed: {e}")
                            # Save error result but continue
                            await _save_error_result(db, run_id, keyword, device, profile, str(e))
                        finally:
                            processed += 1
                            await db.crawl_runs.update_one(
                                {"run_id": run_id},
                                {"$set": {"processed_keywords": processed}},
                            )
                except Exception as e:
                    logger.error(f"Browser failed for device={device}, profile={profile}: {e}")
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass

        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {"$set": {"status": "completed", "finished_at": datetime.utcnow()}},
        )
        logger.info(f"Crawl {run_id} completed. Processed {processed}/{total}")

    except Exception as e:
        logger.error(f"Crawl {run_id} failed: {e}")
        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": "failed",
                    "finished_at": datetime.utcnow(),
                    "error": str(e),
                }
            },
        )


async def _process_keyword(driver, keyword, run_id, device, profile_name):
    """Process a single keyword: search, extract ads, capture, save."""
    db = get_db()

    # Extract ads
    ad_list = search_and_extract_ads(driver, keyword, run_id, device, profile_name)

    # Capture full page screenshot
    screenshot_path = get_screenshot_path(run_id, keyword, device)
    capture_full_page_screenshot(driver, screenshot_path)

    # Save HTML snapshot
    html_path = get_html_path(run_id, keyword, device)
    save_html_snapshot(driver, html_path)

    if not ad_list:
        # Save a "no ads" result
        no_ads = AdResult(
            run_id=run_id,
            keyword=keyword,
            device=device,
            profile_name=profile_name,
            has_ads=False,
            screenshot_path=relative_storage_path(screenshot_path),
            html_path=relative_storage_path(html_path),
        )
        await db.ad_results.insert_one(no_ads.model_dump())
    else:
        for ad in ad_list:
            ad["screenshot_path"] = relative_storage_path(screenshot_path)
            ad["html_path"] = relative_storage_path(html_path)
            result = AdResult(**ad)
            await db.ad_results.insert_one(result.model_dump())

    logger.info(f"Saved {len(ad_list)} ads for '{keyword}' [{device}]")


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
