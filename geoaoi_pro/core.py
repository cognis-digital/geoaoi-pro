"""geoaoi-pro — MIL-STD-2525 / APP-6 symbol-code helpers + AOI math.

Cognis additions only. QGIS is GPL-2/GPL-3. This module is GPL-3.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from cognis_mil import Finding, ScanResult, Severity

# ---- MIL-STD-2525C symbol identification code (SIDC) helpers ----
# SIDC = 15 chars. Pos 1: scheme, 2: affiliation, 3: dimension, ...
# We validate *form*, not real intelligence content.
AFFILIATIONS = {
    "P": "Pending", "U": "Unknown", "F": "Friend", "N": "Neutral",
    "H": "Hostile", "A": "Assumed Friend", "S": "Suspect",
    "G": "Exercise Pending", "W": "Exercise Unknown",
    "M": "Exercise Friend", "D": "Exercise Neutral",
    "L": "Exercise Hostile", "J": "Joker", "K": "Faker", "O": "None",
}
SCHEMES = {
    "S": "Warfighting", "G": "Tactical Graphics", "W": "METOC",
    "I": "Intelligence", "O": "Stability Ops", "E": "Emergency Mgmt",
}


def validate_sidc(sidc: str) -> tuple[bool, list[str]]:
    """Validate the *form* of a MIL-STD-2525C SIDC string."""
    if not isinstance(sidc, str):
        return False, [f"SIDC must be a string, got {type(sidc).__name__}"]
    errs = []
    if len(sidc) != 15:
        errs.append(f"SIDC must be 15 chars (got {len(sidc)})")
    else:
        if sidc[0] not in SCHEMES:
            errs.append(f"Invalid coding scheme: {sidc[0]!r}")
        if sidc[1] not in AFFILIATIONS:
            errs.append(f"Invalid affiliation: {sidc[1]!r}")
    return (len(errs) == 0, errs)


# ---- AOI geometry ----

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS-84 points."""
    for name, val in (("lat1", lat1), ("lon1", lon1), ("lat2", lat2), ("lon2", lon2)):
        if val is None or not isinstance(val, (int, float)):
            raise TypeError(f"haversine_km: {name} must be a number, got {type(val).__name__!r}")
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        raise ValueError(f"Latitude out of range: lat1={lat1}, lat2={lat2}")
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError(f"Longitude out of range: lon1={lon1}, lon2={lon2}")
    R = 6371.0
    a = math.radians(lat2 - lat1) / 2
    b = math.radians(lon2 - lon1) / 2
    h = (
        math.sin(a) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(b) ** 2
    )
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, h))))


def bbox_for_points(points: list[tuple[float, float]]) -> dict:
    """Return a bounding box dict for a list of (lat, lon) tuples.

    Raises ValueError if *points* is empty.
    """
    if not points:
        raise ValueError("bbox_for_points: points list must not be empty")
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return {
        "min_lat": min(lats), "max_lat": max(lats),
        "min_lon": min(lons), "max_lon": max(lons),
    }


def point_in_bbox(pt: tuple[float, float], bbox: dict) -> bool:
    """Return True if *pt* (lat, lon) falls within *bbox*."""
    required = {"min_lat", "max_lat", "min_lon", "max_lon"}
    missing = required - set(bbox.keys())
    if missing:
        raise KeyError(f"bbox dict missing keys: {missing}")
    return (
        bbox["min_lat"] <= pt[0] <= bbox["max_lat"]
        and bbox["min_lon"] <= pt[1] <= bbox["max_lon"]
    )


def _check_coords(coords: object) -> bool:
    """Return True if *coords* is a valid [lon, lat] WGS-84 pair."""
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return False
    try:
        lon, lat = float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return False
    return -180 <= lon <= 180 and -90 <= lat <= 90


# ---- scan: validate a GeoJSON file of MIL-symbols ----

def scan(target: str = ".", **opts) -> ScanResult:
    """Scan a directory or single .geojson file for MIL-STD-2525 symbol issues."""
    r = ScanResult(tool_name="geoaoi-pro", tool_version="0.1.0")
    p = Path(target)

    if not p.exists():
        r.add(Finding(
            "GP-NOTFOUND", Severity.VERY_HIGH,
            f"Target path does not exist: {target}",
            location=str(target),
            remediation="Supply a valid path to a .geojson file or directory.",
        ))
        r.finalize()
        return r

    if p.is_dir():
        files = list(p.glob("*.geojson"))
    elif p.suffix == ".geojson":
        files = [p]
    else:
        r.add(Finding(
            "GP-BADEXT", Severity.LOW,
            f"Target is not a .geojson file and not a directory: {target}",
            location=str(target),
            remediation="Pass a .geojson file or a directory containing .geojson files.",
        ))
        r.finalize()
        return r

    r.items_scanned = len(files)

    if not files:
        r.finalize()
        return r

    for f in files:
        try:
            raw = f.read_text(encoding="utf-8")
        except OSError as e:
            r.add(Finding(
                "GP-READ", Severity.LOW,
                f"Could not read {f}: {e}",
                location=str(f),
            ))
            continue

        try:
            gj = json.loads(raw)
        except json.JSONDecodeError as e:
            r.add(Finding(
                "GP-PARSE", Severity.LOW,
                f"Invalid JSON in {f}: {e}",
                location=str(f),
                remediation="Ensure the file is valid GeoJSON.",
            ))
            continue

        if not isinstance(gj, dict):
            r.add(Finding(
                "GP-PARSE", Severity.LOW,
                f"Expected GeoJSON object in {f}, got {type(gj).__name__}",
                location=str(f),
            ))
            continue

        feats = gj.get("features")
        if feats is None:
            feats = []
        if not isinstance(feats, list):
            r.add(Finding(
                "GP-SCHEMA", Severity.LOW,
                f"'features' must be a list in {f}",
                location=str(f),
            ))
            continue

        for i, feat in enumerate(feats):
            if not isinstance(feat, dict):
                r.add(Finding(
                    f"GP-FEAT-{i}", Severity.LOW,
                    f"Feature {i} is not an object",
                    location=str(f),
                ))
                continue

            props = feat.get("properties") or {}
            sidc = props.get("sidc") or props.get("SIDC") or ""
            if not sidc:
                r.add(Finding(
                    f"GP-NOSIDC-{i}", Severity.MODERATE,
                    "Feature missing SIDC",
                    location=str(f),
                    remediation="Every MIL feature should carry a MIL-STD-2525 SIDC.",
                ))
                continue

            ok, errs = validate_sidc(sidc)
            if not ok:
                r.add(Finding(
                    f"GP-BADSIDC-{i}", Severity.HIGH,
                    f"Invalid SIDC {sidc!r}",
                    location=str(f),
                    description="; ".join(errs),
                ))

            # Coords check — only for Point geometries
            geom = feat.get("geometry")
            if isinstance(geom, dict) and geom.get("type") == "Point":
                coords = geom.get("coordinates")
                if not _check_coords(coords):
                    r.add(Finding(
                        f"GP-COORDS-{i}", Severity.HIGH,
                        f"Out-of-range or malformed coordinates: {coords!r}",
                        location=str(f),
                        remediation="GeoJSON Point coordinates must be [longitude, latitude] "
                                    "within WGS-84 bounds.",
                    ))

    r.finalize()
    return r
