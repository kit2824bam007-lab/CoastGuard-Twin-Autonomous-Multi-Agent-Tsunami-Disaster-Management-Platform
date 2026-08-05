"""
/fetch-data — trigger and inspect earthquake data ingestion.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.orm import Earthquake
from app.models.schemas import EarthquakeOut
from app.services.pipeline import run_ingestion_cycle

logger = logging.getLogger("tsunami.api.data")
router = APIRouter(prefix="/fetch-data", tags=["data"])


@router.post("/", summary="Trigger an on-demand USGS/NOAA ingestion cycle")
async def trigger_fetch():
    try:
        result = await run_ingestion_cycle()
        return {"status": "ok", **result}
    except Exception as e:
        logger.exception("Ingestion cycle failed")
        raise HTTPException(status_code=502, detail=f"Upstream data source error: {e}")


@router.get("/earthquakes", response_model=list[EarthquakeOut], summary="List recent stored earthquakes")
async def list_earthquakes(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(Earthquake).order_by(Earthquake.event_time.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
