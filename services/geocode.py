# services/geocode.py — геокодинг места рождения в (lat, lng, tz_str)
import asyncio
import logging
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)
_geocoder = Nominatim(user_agent="astrobot/1.0", timeout=10)
_tf = TimezoneFinder()
_cache = {}  # place_lower -> (lat, lng, tz_str) | None


async def resolve_birth_place(place: str):
    """Возвращает (lat, lng, tz_str) или (None, None, None)."""
    if not place or not place.strip():
        return (None, None, None)
    key = place.strip().lower()
    if key in _cache:
        return _cache[key] or (None, None, None)
    try:
        locs = await asyncio.to_thread(_geocoder.geocode, place, exactly_one=False, language="ru", limit=5)
    except Exception as e:
        logger.warning(f"geocode fail '{place}': {e}")
        _cache[key] = None
        return (None, None, None)
    if not locs:
        _cache[key] = None
        return (None, None, None)
    # приоритет: Беларусь/Россия/Украина/Казахстан, иначе первый
    preferred = None
    for L in locs:
        addr = (L.address or "").lower()
        if any(x in addr for x in ["беларус", "belarus", "росси", "russia",
                                   "украин", "ukraine", "казахстан", "kazakhstan"]):
            preferred = L
            break
    loc = preferred or locs[0]
    tz = _tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    if not tz:
        _cache[key] = None
        return (None, None, None)
    result = (loc.latitude, loc.longitude, tz)
    _cache[key] = result
    return result