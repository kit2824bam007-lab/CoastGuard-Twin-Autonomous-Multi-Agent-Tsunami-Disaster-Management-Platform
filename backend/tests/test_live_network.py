"""
Live network integration and fallback parsing tests.
"""
import pytest
from app.services.usgs_service import fetch_usgs_feed
from app.services.noaa_service import fetch_active_noaa_bulletins


@pytest.mark.asyncio
async def test_usgs_feed_graceful_fallback():
    """
    Verifies that fetch_usgs_feed returns a valid list of parsed earthquake
    dictionaries, regardless of network connectivity.
    """
    events = await fetch_usgs_feed()
    assert isinstance(events, list)

    if len(events) > 0:
        event = events[0]
        # Verify schema complies with required database input schema properties
        required_keys = ["id", "magnitude", "depth_km", "latitude", "longitude", "place", "source", "event_time"]
        for key in required_keys:
            assert key in event
            
        assert isinstance(event["id"], str)
        assert isinstance(event["magnitude"], float)
        assert isinstance(event["depth_km"], float)
        assert isinstance(event["latitude"], float)
        assert isinstance(event["longitude"], float)
        assert isinstance(event["place"], str)


@pytest.mark.asyncio
async def test_noaa_bulletins_graceful_fallback():
    """
    Verifies that fetch_active_noaa_bulletins returns list of active bulletins with fallback.
    """
    bulletins = await fetch_active_noaa_bulletins()
    assert isinstance(bulletins, list)
    
    # Active NOAA bulletins should show up as strings or empty list
    for b in bulletins:
        assert isinstance(b, str)
