"""
NOAA / NWS Tsunami Warning Center data ingestion.

Real sources:
  1. Tsunami.gov Atom feed (active tsunami messages/bulletins):
       https://www.tsunami.gov/events/xml/PAAQAtom.xml
     (PAAQ = Pacific Tsunami Warning Center; AAAQ = Atlantic; also check
      https://tsunami.gov for the current list of regional feeds)

  2. NOAA NDBC buoy / sea-level data (for ocean-height confirmation), e.g.:
       https://www.ndbc.noaa.gov/data/realtime2/<station_id>.txt
     Station list: https://www.ndbc.noaa.gov/

  3. NOAA CO-OPS water level API (tide stations near coast):
       https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
       ?product=water_level&station=<station_id>&date=latest
       &datum=MLLW&units=metric&time_zone=gmt&format=json

We parse the Atom feed for any currently active bulletins; an offshore
earthquake risk score is boosted if there's an active NOAA bulletin for
the same ocean basin at ingestion time.
"""
import logging
import httpx
import xml.etree.ElementTree as ET
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger("tsunami.noaa")

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_active_noaa_bulletins() -> list[dict]:
    """Fetch and parse active tsunami bulletins from tsunami.gov Atom feed."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(settings.noaa_tsunami_atom_url)
        resp.raise_for_status()
        xml_text = resp.text

    bulletins = []
    try:
        root = ET.fromstring(xml_text)
        for entry in root.findall("atom:entry", ATOM_NS):
            title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
            updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
            summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
            link_el = entry.find("atom:link", ATOM_NS)
            link = link_el.attrib.get("href") if link_el is not None else None
            bulletins.append({
                "title": title,
                "updated": updated,
                "summary": summary,
                "link": link,
            })
    except ET.ParseError as e:
        logger.warning(f"Could not parse NOAA Atom feed: {e}")

    logger.info(f"Fetched {len(bulletins)} active NOAA tsunami bulletins")
    return bulletins


async def fetch_tide_station(station_id: str) -> dict:
    """Fetch real-time water level for a specific NOAA CO-OPS tide station."""
    url = (
        "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        f"?product=water_level&station={station_id}&date=latest"
        "&datum=MLLW&units=metric&time_zone=gmt&format=json"
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
