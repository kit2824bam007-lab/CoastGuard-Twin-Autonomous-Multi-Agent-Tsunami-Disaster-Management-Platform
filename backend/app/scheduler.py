"""
APScheduler background job: polls USGS/NOAA every POLL_INTERVAL_SECONDS.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.services.pipeline import run_ingestion_cycle

logger = logging.getLogger("tsunami.scheduler")
scheduler = AsyncIOScheduler()


async def _job():
    try:
        await run_ingestion_cycle()
    except Exception as e:
        logger.error(f"Ingestion cycle failed: {e}")


def start_scheduler():
    scheduler.add_job(_job, "interval", seconds=settings.poll_interval_seconds, id="ingestion_cycle")
    scheduler.start()
    logger.info(f"Scheduler started — polling every {settings.poll_interval_seconds}s")
