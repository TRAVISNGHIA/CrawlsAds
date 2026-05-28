import asyncio
from datetime import datetime, timezone
from typing import Optional

from database.mongo import get_db
from services.crawler_service import start_auto_crawl_from_db
from core.logger import get_logger

logger = get_logger(__name__)

_scheduler_task: Optional[asyncio.Task] = None
_scheduler_lock = asyncio.Lock()

_is_crawling = False

async def get_scheduler_config() -> dict:
    db = get_db()

    cfg = await db.scheduler_config.find_one({})

    if not cfg:
        return {
            "enabled": False,
            "times_per_day": 4,
            "devices": ["desktop"],
        }

    return cfg


async def get_profiles_from_db() -> list[str]:
    db = get_db()

    cursor = db.profiles.find(
        {},
        {
            "profile_directory": 1,
            "_id": 0,
        },
    )

    docs = await cursor.to_list(length=None)

    profiles = [
        doc["profile_directory"]
        for doc in docs
        if doc.get("profile_directory")
    ]

    return profiles

async def _run_crawl(
    devices: list[str],
    profiles: list[str],
):
    global _is_crawling

    async with _scheduler_lock:

        if _is_crawling:
            logger.warning("⚠️ Crawl đang chạy, bỏ qua job mới.")
            return

        _is_crawling = True

        try:
            logger.info(
                f"🚀 Bắt đầu crawl | profiles={profiles} | devices={devices}"
            )

            started_at = datetime.now(timezone.utc)

            run_id = await start_auto_crawl_from_db(
                devices=devices,
                profiles=profiles,
            )

            finished_at = datetime.now(timezone.utc)

            db = get_db()

            await db.scheduler_config.update_one(
                {},
                {
                    "$set": {
                        "last_run_at": finished_at,
                        "last_run_id": run_id,
                        "last_duration_seconds": (
                            finished_at - started_at
                        ).total_seconds(),
                    }
                },
                upsert=True,
            )

            if run_id:
                logger.info(f"✅ Crawl hoàn tất | run_id={run_id}")
            else:
                logger.warning("⚠️ Không có keyword để crawl")

        except Exception as e:
            logger.error(
                f"❌ Crawl lỗi: {e}",
                exc_info=True,
            )

        finally:
            _is_crawling = False

async def _scheduler_loop():
    logger.info("⏰ Scheduler started")

    first_run = True

    while True:

        try:
            cfg = await get_scheduler_config()

            enabled = cfg.get("enabled", False)

            if not enabled:
                await asyncio.sleep(30)
                continue

            times_per_day = max(
                1,
                cfg.get("times_per_day", 4),
            )

            interval_seconds = (
                24 * 3600
            ) / times_per_day

            devices = cfg.get("devices") or ["desktop"]

            profiles = await get_profiles_from_db()

            if not profiles:
                logger.warning(
                    "⚠️ Không có profile nào trong DB."
                )

                await asyncio.sleep(60)
                continue

            if first_run:
                logger.info("🚀 First scheduler run")
                first_run = False
            else:
                logger.info("⏰ Scheduled crawl trigger")

            await _run_crawl(
                devices=devices,
                profiles=profiles,
            )

            # responsive sleep
            slept = 0

            while slept < interval_seconds:
                await asyncio.sleep(30)
                slept += 30

        except asyncio.CancelledError:
            logger.info("🛑 Scheduler stopped")
            break

        except Exception as e:
            logger.error(
                f"❌ Scheduler loop error: {e}",
                exc_info=True,
            )

            await asyncio.sleep(60)

def start_scheduler():
    global _scheduler_task

    if _scheduler_task and not _scheduler_task.done():
        logger.warning("⚠️ Scheduler already running")
        return

    loop = asyncio.get_running_loop()

    _scheduler_task = loop.create_task(
        _scheduler_loop()
    )

    logger.info("✅ Scheduler task created")

def stop_scheduler():
    global _scheduler_task

    if (
        _scheduler_task
        and not _scheduler_task.done()
    ):
        _scheduler_task.cancel()

        logger.info("🛑 Scheduler stop requested")