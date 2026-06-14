"""Tests for hardened error-handling and edge-case paths."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from geoaoi_pro.core import (
    bbox_for_points,
    haversine_km,
    point_in_bbox,
    scan,
    validate_sidc,
)


# ---------------------------------------------------------------------------
# validate_sidc edge cases
# ---------------------------------------------------------------------------

def test_sidc_non_string_input():
    """Non-string SIDC returns a clear error, no exception."""
    ok, errs = validate_sidc(12345)  # type: ignore[arg-type]
    assert not ok
    assert errs


def test_sidc_empty_string():
    ok, errs = validate_sidc("")
    assert not ok
    assert any("15 chars" in e for e in errs)


# ---------------------------------------------------------------------------
# haversine_km validation
# ---------------------------------------------------------------------------

def test_haversine_none_raises():
    with pytest.raises(TypeError):
        haversine_km(None, 0.0, 0.0, 0.0)  # type: ignore[arg-type]


def test_haversine_string_raises():
    with pytest.raises(TypeError):
        haversine_km(38.89, -77.04, "bad", -77.05)  # type: ignore[arg-type]


def test_haversine_lat_out_of_range():
    with pytest.raises(ValueError):
        haversine_km(91.0, 0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# bbox_for_points edge case — empty list
# ---------------------------------------------------------------------------

def test_bbox_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        bbox_for_points([])


def test_bbox_single_point():
    bb = bbox_for_points([(10.0, 20.0)])
    assert bb["min_lat"] == bb["max_lat"] == 10.0
    assert bb["min_lon"] == bb["max_lon"] == 20.0


# ---------------------------------------------------------------------------
# point_in_bbox — missing keys guard
# ---------------------------------------------------------------------------

def test_point_in_bbox_missing_key():
    with pytest.raises(KeyError):
        point_in_bbox((0.0, 0.0), {"min_lat": 0.0})


# ---------------------------------------------------------------------------
# scan — non-existent target
# ---------------------------------------------------------------------------

def test_scan_missing_path():
    r = scan("/no/such/path/at/all")
    ids = {f.id for f in r.findings}
    assert "GP-NOTFOUND" in ids
    # Should still finalize without raising
    assert r.composite_score >= 0


def test_scan_wrong_extension():
    """A .txt file should produce GP-BADEXT, not a crash."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        r = scan(tmp_path)
        ids = {f.id for f in r.findings}
        assert "GP-BADEXT" in ids
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# scan — empty directory (no .geojson files)
# ---------------------------------------------------------------------------

def test_scan_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = scan(tmpdir)
        assert r.items_scanned == 0
        assert r.findings == []


# ---------------------------------------------------------------------------
# scan — malformed JSON
# ---------------------------------------------------------------------------

def test_scan_malformed_json():
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as tmp:
        tmp.write("{ not valid json }")
        tmp_path = tmp.name
    try:
        r = scan(tmp_path)
        ids = {f.id for f in r.findings}
        assert any("GP-PARSE" in fid for fid in ids)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# scan — null geometry (no crash)
# ---------------------------------------------------------------------------

def test_scan_null_geometry():
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": None,
                "properties": {"sidc": "SFGPUCI-----E--"},
            }
        ],
    }
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as tmp:
        json.dump(gj, tmp)
        tmp_path = tmp.name
    try:
        r = scan(tmp_path)
        # No findings about bad coordinates — null geometry is silently skipped
        coord_findings = [f for f in r.findings if "COORDS" in f.id]
        assert coord_findings == []
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# scan — malformed coordinates (too few values)
# ---------------------------------------------------------------------------

def test_scan_malformed_coordinates():
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [999]},
                "properties": {"sidc": "SFGPUCI-----E--"},
            }
        ],
    }
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as tmp:
        json.dump(gj, tmp)
        tmp_path = tmp.name
    try:
        r = scan(tmp_path)
        coord_findings = [f for f in r.findings if "COORDS" in f.id]
        assert coord_findings, "Expected a GP-COORDS finding for [999]"
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# scan — empty features list produces no findings (clean file)
# ---------------------------------------------------------------------------

def test_scan_empty_features():
    gj = {"type": "FeatureCollection", "features": []}
    with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as tmp:
        json.dump(gj, tmp)
        tmp_path = tmp.name
    try:
        r = scan(tmp_path)
        assert r.findings == []
    finally:
        os.unlink(tmp_path)
