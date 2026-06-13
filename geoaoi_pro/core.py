"""geoaoi-pro — MIL-STD-2525 / APP-6 symbol-code helpers + AOI math.

Cognis additions only. QGIS is GPL-2/GPL-3. This module is GPL-3.
"""
from __future__ import annotations
import math, json
from pathlib import Path
from cognis_mil import ScanResult, Finding, Severity

# ---- MIL-STD-2525C symbol identification code (SIDC) helpers ----
# SIDC = 15 chars. Pos 1: scheme, 2: affiliation, 3: dimension, ...
# We validate *form*, not real intelligence content.
AFFILIATIONS = {"P":"Pending","U":"Unknown","F":"Friend","N":"Neutral","H":"Hostile",
                "A":"Assumed Friend","S":"Suspect","G":"Exercise Pending","W":"Exercise Unknown",
                "M":"Exercise Friend","D":"Exercise Neutral","L":"Exercise Hostile","J":"Joker","K":"Faker","O":"None"}
SCHEMES = {"S":"Warfighting","G":"Tactical Graphics","W":"METOC","I":"Intelligence","O":"Stability Ops","E":"Emergency Mgmt"}

def validate_sidc(sidc: str) -> tuple[bool, list[str]]:
    errs = []
    if len(sidc) != 15: errs.append(f"SIDC must be 15 chars (got {len(sidc)})")
    else:
        if sidc[0] not in SCHEMES:      errs.append(f"Invalid coding scheme: {sidc[0]}")
        if sidc[1] not in AFFILIATIONS: errs.append(f"Invalid affiliation: {sidc[1]}")
    return (len(errs) == 0, errs)

# ---- AOI geometry ----
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    a = math.radians(lat2-lat1)/2; b = math.radians(lon2-lon1)/2
    h = math.sin(a)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(b)**2
    return 2 * R * math.asin(math.sqrt(h))

def bbox_for_points(points: list[tuple[float,float]]) -> dict:
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    return {"min_lat": min(lats), "max_lat": max(lats),
            "min_lon": min(lons), "max_lon": max(lons)}

def point_in_bbox(pt: tuple[float,float], bbox: dict) -> bool:
    return (bbox["min_lat"] <= pt[0] <= bbox["max_lat"]
            and bbox["min_lon"] <= pt[1] <= bbox["max_lon"])

# ---- scan: validate a GeoJSON file of MIL-symbols ----
def scan(target=".", **opts):
    r = ScanResult(tool_name="geoaoi-pro", tool_version="0.1.0")
    p = Path(target)
    files = list(p.glob("*.geojson")) if p.is_dir() else ([p] if p.suffix == ".geojson" else [])
    r.items_scanned = len(files)
    for f in files:
        try: gj = json.loads(f.read_text())
        except Exception as e:
            r.add(Finding("GP-PARSE", Severity.LOW, f"Couldn't parse {f}: {e}", location=str(f))); continue
        feats = gj.get("features", [])
        for i, feat in enumerate(feats):
            props = feat.get("properties", {})
            sidc = props.get("sidc") or props.get("SIDC") or ""
            if not sidc:
                r.add(Finding(f"GP-NOSIDC-{i}", Severity.MODERATE,
                              "Feature missing SIDC", location=str(f),
                              remediation="Every MIL feature should carry a MIL-STD-2525 SIDC."))
                continue
            ok, errs = validate_sidc(sidc)
            if not ok:
                r.add(Finding(f"GP-BADSIDC-{i}", Severity.HIGH,
                              f"Invalid SIDC '{sidc}'", location=str(f),
                              description="; ".join(errs)))
            # Coords check
            geom = feat.get("geometry", {})
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [None,None])
                if not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
                    r.add(Finding(f"GP-COORDS-{i}", Severity.HIGH,
                                  f"Out-of-range coordinates: {coords}", location=str(f)))
    r.finalize(); return r
