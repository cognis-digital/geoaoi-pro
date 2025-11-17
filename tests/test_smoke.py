from pathlib import Path
from geoaoi_pro.core import validate_sidc, haversine_km, scan, bbox_for_points
D = Path(__file__).parent.parent / "demos"
def test_sidc_valid():
    assert validate_sidc("SFGPUCI-----E--")[0] is True
def test_sidc_invalid():
    ok, errs = validate_sidc("BAD")
    assert not ok and len(errs) > 0
def test_haversine():
    d = haversine_km(38.89, -77.04, 38.90, -77.05)
    assert 0.5 < d < 2.0  # ~1.4km
def test_scan_demo():
    r = scan(str(D))
    ids = {f.id for f in r.findings}
    assert any("NOSIDC" in i for i in ids)
    assert any("BADSIDC" in i for i in ids)
