"""Edge case tests."""

import tempfile
import zipfile
from pathlib import Path
import fiona
from shapely.geometry import Polygon, mapping
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_unsupported_geometry_graceful():
    tmp_dir = Path(tempfile.mkdtemp())
    shp_path = tmp_dir / "single.shp"
    schema = {"geometry": "Polygon", "properties": {}}
    with fiona.open(
        str(shp_path), "w", driver="ESRI Shapefile", schema=schema, crs="EPSG:4326"
    ) as dst:
        dst.write(
            {
                "geometry": mapping(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])),
                "properties": {},
            }
        )

    zip_path = tmp_dir / "single.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        for f in tmp_dir.iterdir():
            if f.name != "single.zip":
                zf.write(f, f.name)

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/", files={"file": ("single.zip", f, "application/zip")}
        )
    assert response.status_code == 201, f"Body: {response.text}"


def test_empty_kml():
    tmp_dir = Path(tempfile.mkdtemp())
    kml_path = tmp_dir / "empty.kml"
    kml_path.write_text(
        """<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document></Document></kml>"""
    )

    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("empty.kml", f, "application/vnd.google-earth.kml+xml")},
        )
    assert response.status_code == 201
    assert response.json()["feature_count"] == 0
