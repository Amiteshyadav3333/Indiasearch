"""Location-aware nearby place search backed by OpenStreetMap."""

import logging
import math
import re

import aiohttp

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "IndiaSearch/1.0 (https://indiasearch.site)"}
LOCAL_TERMS = (
    "near me", "nearby", "around me", "closest", "nearest", "local",
    "पास", "नज़दीक", "नजदीक", "करीब", "paas", "pass", "nazdeek", "najdik",
)
PLACE_TYPES = {
    "restaurant": ("amenity", ["restaurant", "fast_food", "food_court"]),
    "restaurants": ("amenity", ["restaurant", "fast_food", "food_court"]),
    "restorent": ("amenity", ["restaurant", "fast_food", "food_court"]),
    "रेस्टोरेंट": ("amenity", ["restaurant", "fast_food", "food_court"]),
    "hotel": ("tourism", ["hotel", "guest_house", "hostel"]),
    "होटल": ("tourism", ["hotel", "guest_house", "hostel"]),
    "hospital": ("amenity", ["hospital", "clinic", "doctors"]),
    "अस्पताल": ("amenity", ["hospital", "clinic", "doctors"]),
    "cafe": ("amenity", ["cafe"]),
    "coffee": ("amenity", ["cafe"]),
    "petrol": ("amenity", ["fuel"]),
    "fuel": ("amenity", ["fuel"]),
    "atm": ("amenity", ["atm", "bank"]),
    "bank": ("amenity", ["bank"]),
    "pharmacy": ("amenity", ["pharmacy"]),
    "medical": ("amenity", ["pharmacy", "clinic"]),
    "school": ("amenity", ["school"]),
    "college": ("amenity", ["college", "university"]),
    "mechanic": ("shop", ["car_repair", "motorcycle_repair"]),
}


def is_local_query(query: str) -> bool:
    q = (query or "").casefold()
    return any(term in q for term in LOCAL_TERMS) or any(term in q for term in PLACE_TYPES)


def _place_filter(query: str):
    q = (query or "").casefold()
    for term, value in PLACE_TYPES.items():
        if term in q:
            return value
    return None


def _distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def reverse_geocode(lat: float, lon: float) -> dict:
    params = {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 14, "addressdetails": 1}
    try:
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.get("https://nominatim.openstreetmap.org/reverse", params=params) as response:
                if response.status != 200:
                    return {}
                data = await response.json()
        address = data.get("address") or {}
        city = (
            address.get("city") or address.get("town") or address.get("village")
            or address.get("municipality") or address.get("county") or ""
        )
        state = address.get("state") or ""
        return {
            "city": city, "state": state,
            "label": ", ".join(part for part in (city, state) if part),
            "display_name": data.get("display_name", ""),
        }
    except Exception as exc:
        logger.warning("[Local] Reverse geocoding failed: %s", exc)
        return {}


async def geocode_query_location(query: str) -> dict:
    cleaned = re.sub(
        r"\b(near me|nearby|around me|closest|nearest|local|restaurant|restaurants|restorent|hotel|hospital|cafe|coffee|petrol|atm|bank|pharmacy|medical|school|college|mechanic|paas|pass|near|in)\b",
        " ", query, flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,-")
    if len(cleaned) < 3:
        return {}
    try:
        params = {"q": f"{cleaned}, India", "format": "jsonv2", "limit": 5, "countrycodes": "in"}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.get("https://nominatim.openstreetmap.org/search", params=params) as response:
                rows = await response.json() if response.status == 200 else []
        if rows:
            row = next(
                (item for item in rows if item.get("addresstype") in {"city", "town", "village", "municipality"}),
                rows[0],
            )
            return {"lat": float(row["lat"]), "lon": float(row["lon"]), "label": row.get("display_name", cleaned)}
    except Exception as exc:
        logger.warning("[Local] Nominatim geocoding failed: %s", exc)

    # Independent fallback prevents one public geocoder outage from disabling
    # named-city local search.
    try:
        params = {"q": f"{cleaned}, India", "limit": 1}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.get("https://photon.komoot.io/api/", params=params) as response:
                payload = await response.json() if response.status == 200 else {}
        features = payload.get("features") or []
        if features:
            feature = features[0]
            lon, lat = feature["geometry"]["coordinates"]
            props = feature.get("properties") or {}
            label = ", ".join(part for part in (
                props.get("name"), props.get("city"), props.get("state"), props.get("country")
            ) if part)
            return {"lat": float(lat), "lon": float(lon), "label": label or cleaned}
    except Exception as exc:
        logger.warning("[Local] Photon geocoding failed: %s", exc)
    return {}


async def search_nearby(query: str, lat: float, lon: float, radius_m: int = 12000, limit: int = 12) -> list:
    place_filter = _place_filter(query)
    if not place_filter:
        return []
    key, values = place_filter
    selectors = "".join(f'nwr(around:{radius_m},{lat},{lon})["{key}"="{value}"];' for value in values)
    overpass_query = f"[out:json][timeout:12];({selectors});out center tags;"
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.post("https://overpass-api.de/api/interpreter", data={"data": overpass_query}) as response:
                if response.status != 200:
                    payload = {}
                else:
                    payload = await response.json()
    except Exception as exc:
        logger.warning("[Local] Nearby place search failed: %s", exc)
        payload = {}

    results = []
    for item in payload.get("elements", []):
        tags = item.get("tags") or {}
        name = tags.get("name") or tags.get("name:en") or tags.get("brand")
        center = item.get("center") or item
        item_lat, item_lon = center.get("lat"), center.get("lon")
        if not name or item_lat is None or item_lon is None:
            continue
        distance = _distance_km(lat, lon, float(item_lat), float(item_lon))
        address = ", ".join(part for part in (
            tags.get("addr:housenumber"), tags.get("addr:street"),
            tags.get("addr:suburb"), tags.get("addr:city"),
        ) if part)
        category = tags.get("amenity") or tags.get("tourism") or tags.get("shop") or "place"
        details = [f"{distance:.1f} km away", category.replace("_", " ")]
        if address:
            details.append(address)
        if tags.get("opening_hours"):
            details.append(f"Hours: {tags['opening_hours']}")
        osm_type, osm_id = item.get("type", "node"), item.get("id")
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={item_lat},{item_lon}"
        results.append({
            "title": name,
            "url": directions_url,
            "source_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
            "snippet": " · ".join(details),
            "source": "openstreetmap",
            "distance_km": round(distance, 2),
            "latitude": float(item_lat), "longitude": float(item_lon),
            "maps_url": directions_url,
            "category": category,
            "_boost": max(0, 8 - distance),
        })
    results.sort(key=lambda row: row["distance_km"])
    if results:
        return results[:limit]
    return await _search_nominatim_nearby(query, lat, lon, limit)


async def _search_nominatim_nearby(query: str, lat: float, lon: float, limit: int) -> list:
    """Fallback POI search when the Overpass endpoint is busy or unavailable."""
    place_filter = _place_filter(query)
    if not place_filter:
        return []
    category = place_filter[1][0].replace("_", " ")
    delta = 0.14
    params = {
        "q": category,
        "format": "jsonv2",
        "limit": min(limit * 2, 30),
        "addressdetails": 1,
        "bounded": 1,
        "viewbox": f"{lon-delta},{lat+delta},{lon+delta},{lat-delta}",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.get("https://nominatim.openstreetmap.org/search", params=params) as response:
                rows = await response.json() if response.status == 200 else []
    except Exception as exc:
        logger.warning("[Local] Nearby Nominatim fallback failed: %s", exc)
        return []

    results = []
    for row in rows:
        name = row.get("name") or (row.get("display_name") or "").split(",")[0]
        if not name:
            continue
        item_lat, item_lon = float(row["lat"]), float(row["lon"])
        distance = _distance_km(lat, lon, item_lat, item_lon)
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={item_lat},{item_lon}"
        results.append({
            "title": name,
            "url": directions_url,
            "source_url": f"https://www.openstreetmap.org/{row.get('osm_type', 'node')}/{row.get('osm_id', '')}",
            "snippet": f"{distance:.1f} km away · {category} · {row.get('display_name', '')}",
            "source": "openstreetmap",
            "distance_km": round(distance, 2),
            "latitude": item_lat,
            "longitude": item_lon,
            "maps_url": directions_url,
            "category": category,
        })
    results.sort(key=lambda item: item["distance_km"])
    return results[:limit]


async def resolve_location(query: str, lat=None, lon=None) -> dict:
    if lat is not None and lon is not None:
        details = await reverse_geocode(float(lat), float(lon))
        return {"lat": float(lat), "lon": float(lon), **details}
    return await geocode_query_location(query)
