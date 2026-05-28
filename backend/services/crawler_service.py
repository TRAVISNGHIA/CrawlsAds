
import asyncio
import random
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.logger import get_logger
from database.models import AdResult, CrawlRun, CrawlStartRequest
from database.mongo import get_db
from services.ad_extractor import search_and_extract_ads
from services.browser_factory import create_browser
from services.capture_service import (
    capture_full_page_screenshot,
    save_html_snapshot,
)
from utils.file_utils import (
    get_html_path,
    get_screenshot_path,
    relative_storage_path,
)

logger = get_logger(__name__)

BROWSER_EXECUTOR = ThreadPoolExecutor(max_workers=4)

_active_crawl_tasks: Dict[str, asyncio.Task] = {}

async def start_crawl_job(
    request: CrawlStartRequest,
) -> str:

    run_id = str(uuid.uuid4())

    db = get_db()

    keywords = (
        request.keywords
        if isinstance(request.keywords, list)
        else [request.keywords]
    )

    devices = (
        request.devices
        if isinstance(request.devices, list)
        else [request.devices]
    )

    profiles = (
        request.profiles
        if isinstance(request.profiles, list)
        else [request.profiles]
    )

    total_keywords = (
        len(keywords)
        * len(devices)
        * len(profiles)
    )

    run = CrawlRun(
        run_id=run_id,
        status="pending",
        total_keywords=total_keywords,
        processed_keywords=0,
        devices=devices,
        profiles=profiles,
        started_at=datetime.now(timezone.utc),
    )

    await db.crawl_runs.insert_one(
        run.model_dump()
    )

    logger.info(
        f"🚀 Crawl job created: {run_id}"
    )

    task = asyncio.create_task(
        _run_crawl_async(
            run_id=run_id,
            keywords=keywords,
            devices=devices,
            profiles=profiles,
        )
    )

    _active_crawl_tasks[run_id] = task

    return run_id


async def start_auto_crawl_from_db(
    devices: Optional[List[str]] = None,
    profiles: Optional[List[str]] = None,
) -> Optional[str]:

    db = get_db()

    cursor = db.keywords.find(
        {
            "enabled": {"$ne": False},
        },
        {
            "keyword": 1,
            "_id": 0,
        },
    )

    keyword_docs = await cursor.to_list(
        length=None
    )

    keywords = [
        doc["keyword"].strip()
        for doc in keyword_docs
        if doc.get("keyword")
    ]

    if not keywords:
        logger.warning(
            "⚠️ Không tìm thấy keyword nào"
        )
        return None

    if not profiles:
        raise ValueError(
            "No browser profiles provided"
        )

    devices = devices or ["desktop"]

    logger.info(
        f"🚀 Auto crawl start | "
        f"keywords={len(keywords)} | "
        f"devices={devices} | "
        f"profiles={profiles}"
    )

    request = CrawlStartRequest(
        keywords=keywords,
        devices=devices,
        profiles=profiles,
    )

    return await start_crawl_job(request)

async def _run_crawl_async(
    run_id: str,
    keywords: List[str],
    devices: List[str],
    profiles: List[str],
):

    db = get_db()

    loop = asyncio.get_running_loop()

    processed = 0

    total = (
        len(keywords)
        * len(devices)
        * len(profiles)
    )

    await db.crawl_runs.update_one(
        {"run_id": run_id},
        {
            "$set": {
                "status": "running",
                "error": None,
            }
        },
    )

    try:

        for device in devices:

            for profile in profiles:

                driver = None

                logger.info(
                    f"🌐 Starting browser | "
                    f"device={device} | "
                    f"profile={profile}"
                )

                try:

                    driver = await asyncio.wait_for(
                        loop.run_in_executor(
                            BROWSER_EXECUTOR,
                            create_browser,
                            device,
                            profile,
                        ),
                        timeout=120,
                    )

                    logger.info(
                        f"✅ Browser ready | "
                        f"device={device} | "
                        f"profile={profile}"
                    )

                    for index, keyword in enumerate(keywords):

                        try:

                            docs = await asyncio.wait_for(
                                loop.run_in_executor(
                                    BROWSER_EXECUTOR,
                                    _process_keyword_sync,
                                    driver,
                                    keyword,
                                    run_id,
                                    device,
                                    profile,
                                ),
                                timeout=300,
                            )

                            if docs:
                                try:
                                    await db.ad_results.insert_many(
                                        docs,
                                        ordered=False,
                                    )
                                except Exception as insert_error:
                                    logger.error(
                                        f"❌ Mongo insert error | "
                                        f"keyword={keyword} | "
                                        f"error={insert_error}"
                                    )

                        except asyncio.TimeoutError:

                            logger.error(
                                f"⏰ Timeout | "
                                f"keyword={keyword} | "
                                f"device={device} | "
                                f"profile={profile}"
                            )

                            await _save_error_result(
                                db=db,
                                run_id=run_id,
                                keyword=keyword,
                                device=device,
                                profile_name=profile,
                                error_msg="Timeout during crawl",
                            )

                        except Exception as keyword_error:

                            logger.error(
                                f"❌ Keyword failed | "
                                f"keyword={keyword} | "
                                f"device={device} | "
                                f"profile={profile} | "
                                f"error={keyword_error}",
                                exc_info=True,
                            )

                            await _save_error_result(
                                db=db,
                                run_id=run_id,
                                keyword=keyword,
                                device=device,
                                profile_name=profile,
                                error_msg=str(keyword_error),
                            )

                        finally:

                            processed += 1

                            await db.crawl_runs.update_one(
                                {"run_id": run_id},
                                {
                                    "$set": {
                                        "processed_keywords": processed,
                                    }
                                },
                            )

                        # random delay
                        if index < len(keywords) - 1:

                            delay = random.uniform(4, 9)

                            logger.info(
                                f"😴 Sleep {delay:.1f}s"
                            )

                            await asyncio.sleep(delay)

                except Exception as browser_error:

                    logger.error(
                        f"❌ Browser failed | "
                        f"device={device} | "
                        f"profile={profile} | "
                        f"error={browser_error}",
                        exc_info=True,
                    )

                    for keyword in keywords:

                        processed += 1

                        await _save_error_result(
                            db=db,
                            run_id=run_id,
                            keyword=keyword,
                            device=device,
                            profile_name=profile,
                            error_msg=str(browser_error),
                        )

                        await db.crawl_runs.update_one(
                            {"run_id": run_id},
                            {
                                "$set": {
                                    "processed_keywords": processed,
                                }
                            },
                        )

                finally:

                    if driver:

                        try:

                            await loop.run_in_executor(
                                BROWSER_EXECUTOR,
                                _safe_quit,
                                driver,
                            )

                            logger.info(
                                f"🛑 Browser closed | "
                                f"device={device} | "
                                f"profile={profile}"
                            )

                        except Exception as quit_error:

                            logger.error(
                                f"❌ Browser quit failed | "
                                f"error={quit_error}"
                            )

        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": "completed",
                    "processed_keywords": processed,
                    "finished_at": datetime.now(
                        timezone.utc
                    ),
                }
            },
        )

        logger.info(
            f"✅ Crawl completed | "
            f"run_id={run_id} | "
            f"{processed}/{total}"
        )

    except Exception as e:

        logger.error(
            f"❌ Crawl failed | "
            f"run_id={run_id} | "
            f"error={e}",
            exc_info=True,
        )

        await db.crawl_runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": "failed",
                    "finished_at": datetime.now(
                        timezone.utc
                    ),
                    "error": str(e),
                }
            },
        )

    finally:

        _active_crawl_tasks.pop(
            run_id,
            None,
        )

def _process_keyword_sync(
    driver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Any]]:

    ad_list = search_and_extract_ads(
        driver,
        keyword,
        run_id,
        device,
        profile_name,
    )

    screenshot_rel_path = None
    html_rel_path = None

    # screenshot
    try:

        screenshot_path = get_screenshot_path(
            run_id,
            keyword,
            device,
        )

        capture_full_page_screenshot(
            driver,
            screenshot_path,
        )

        screenshot_rel_path = relative_storage_path(
            screenshot_path
        )

    except Exception as e:

        logger.error(
            f"❌ Screenshot failed | "
            f"keyword={keyword} | "
            f"error={e}"
        )

    # html snapshot
    try:

        html_path = get_html_path(
            run_id,
            keyword,
            device,
        )

        save_html_snapshot(
            driver,
            html_path,
        )

        html_rel_path = relative_storage_path(
            html_path
        )

    except Exception as e:

        logger.error(
            f"❌ HTML snapshot failed | "
            f"keyword={keyword} | "
            f"error={e}"
        )

    docs: List[Dict[str, Any]] = []

    if not ad_list:

        no_ads = AdResult(
            run_id=run_id,
            keyword=keyword,
            device=device,
            profile_name=profile_name,
            has_ads=False,
            screenshot_path=screenshot_rel_path,
            html_path=html_rel_path,
        )

        docs.append(
            no_ads.model_dump()
        )

    else:

        for ad in ad_list:

            ad["screenshot_path"] = (
                screenshot_rel_path
            )

            ad["html_path"] = (
                html_rel_path
            )

            docs.append(
                AdResult(**ad).model_dump()
            )

    logger.info(
        f"✅ Processed '{keyword}' "
        f"[{device}] — {len(ad_list)} ads"
    )

    return docs

async def _save_error_result(
    db,
    run_id,
    keyword,
    device,
    profile_name,
    error_msg,
):

    result = AdResult(
        run_id=run_id,
        keyword=keyword,
        device=device,
        profile_name=profile_name,
        has_ads=False,
        advertiser=f"ERROR: {error_msg[:200]}",
    )

    await db.ad_results.insert_one(
        result.model_dump()
    )

def _safe_quit(driver):

    try:
        driver.quit()
    except Exception:
        pass

