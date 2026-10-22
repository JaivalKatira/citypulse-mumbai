"""
OpenStreetMap helpers (no API key needed)
  • Nominatim  -> geocode locality names / search places
  • Overpass   -> find police stations around a point

Usage policy notes:
  Nominatim: max 1 request/second + a real User-Agent  (https://operations.osmfoundation.org/policies/nominatim/)
  Overpass : be gentle, cache results.
"""
import time
from math import radians, sin, cos, sqrt, atan2

import pandas as pd
import requests

USER_AGENT = "MumbaiWomenSafetyApp/1.0 (streamlit community project)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Greater Mumbai bounding box  (left, top, right, bottom)
MUMBAI_VIEWBOX = "72.76,19.30,73.02,18.86"
MUMBAI_CENTER = (19.0760, 72.8777)

_last_call = 0.0


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi, dlam = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlam / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _throttle(min_gap: float = 1.1):
    """Keep at least `min_gap` seconds between Nominatim calls."""
    global _last_call
    wait = min_gap - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def nominatim_search(query: str, limit: int = 5, bounded: bool = True):
    """Return list of dicts {lat, lon, name}; None if the request itself failed."""
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": limit,
        "countrycodes": "in",
        "viewbox": MUMBAI_VIEWBOX,
        "bounded": 1 if bounded else 0,
    }
    for attempt in range(2):
        try:
            _throttle()
            r = requests.get(NOMINATIM_URL, params=params,
                             headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                return [
                    {"lat": float(x["lat"]), "lon": float(x["lon"]),
                     "name": x.get("display_name", query)}
                    for x in r.json()
                ]
            if r.status_code in (429, 503):
                time.sleep(3)
        except Exception:
            time.sleep(1)
    return None


def geocode_locality(name: str, anchor=None):
    """
    Geocode a Mumbai locality.
    anchor = (lat, lon) of the previous (neighbouring) row. It is used only to
    choose between several OSM matches, because the dataset has repeated names
    (e.g. 'Poonam Nagar' exists in more than one ward).
    Returns (status, lat, lon) with status in {"ok", "notfound", "error"}.
    """
    for q in (f"{name}, Mumbai, Maharashtra, India", f"{name}, Mumbai"):
        res = nominatim_search(q)
        if res is None:
            return "error", None, None
        if res:
            if anchor:
                res.sort(key=lambda c: haversine_km(anchor[0], anchor[1], c["lat"], c["lon"]))
            return "ok", res[0]["lat"], res[0]["lon"]
    return "notfound", None, None


def search_place(query: str, limit: int = 5):
    """Free-text place/address search inside Mumbai. Returns list or None on error."""
    q = query if "mumbai" in query.lower() else f"{query}, Mumbai"
    return nominatim_search(q, limit=limit)


def find_police_stations(lat: float, lon: float, radius_m: int = 5000):
    """Police stations near a point from OpenStreetMap (Overpass). None on failure."""
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="police"](around:{radius_m},{lat},{lon});
      way["amenity"="police"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": query},
                              headers={"User-Agent": USER_AGENT}, timeout=30)
            if r.status_code != 200:
                continue
            rows = []
            for el in r.json().get("elements", []):
                la = el.get("lat") or el.get("center", {}).get("lat")
                lo = el.get("lon") or el.get("center", {}).get("lon")
                if la is None or lo is None:
                    continue
                tags = el.get("tags", {})
                rows.append({
                    "name": tags.get("name:en") or tags.get("name") or "Police Station (unnamed in OSM)",
                    "lat": la, "lon": lo,
                    "phone": tags.get("phone") or tags.get("contact:phone") or "",
                })
            df = pd.DataFrame(rows, columns=["name", "lat", "lon", "phone"])
            return df.drop_duplicates(subset=["name", "lat", "lon"]).reset_index(drop=True)
        except Exception:
            continue
    return None
