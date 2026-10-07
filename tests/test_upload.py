"""Upload endpoint tests."""

import tempfile
from pathlib import Path
from tests.fixtures.shapefile import create_polygon_shapefile_zip, create_kml
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_shapefile_zip():
    zip_path = create_polygon_shapefile_zip()
    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/files/", files={"file": ("test.zip", f, "application/zip")}
        )
    assert response.status_code == 201, f"Body: {response.text}"
    data = response.json()
    assert data["filename"] == "test.zip"
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"
    assert data["crs"] is not None


def test_upload_kml():
    kml_path = create_kml()
    with open(kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")},
        )
    assert response.status_code == 201, f"Body: {response.text}"
    data = response.json()
    assert data["filename"] == "test.kml"
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"


def test_upload_invalid_extension():
    tmp = Path(tempfile.mkdtemp()) / "test.txt"
    tmp.write_text("not a geospatial file")
    with open(tmp, "rb") as f:
        response = client.post(
            "/api/files/", files={"file": ("test.txt", f, "text/plain")}
        )
    assert response.status_code == 400


def test_upload_no_file():
    response = client.post("/api/files/")
    assert response.status_code == 422
