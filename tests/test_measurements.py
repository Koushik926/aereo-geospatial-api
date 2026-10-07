"""Measurement endpoint tests."""

from tests.fixtures.shapefile import create_polygon_shapefile_zip
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_file_info():
    zip_path = create_polygon_shapefile_zip()
    with open(zip_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/", files={"file": ("test.zip", f, "application/zip")}
        )
    file_id = upload_resp.json()["id"]

    response = client.get(f"/api/files/{file_id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"


def test_get_file_info_not_found():
    response = client.get("/api/files/nonexistent/")
    assert response.status_code == 404


def test_get_measurements():
    zip_path = create_polygon_shapefile_zip()
    with open(zip_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/", files={"file": ("test.zip", f, "application/zip")}
        )
    file_id = upload_resp.json()["id"]

    response = client.get(f"/api/files/{file_id}/measurements/")
    assert response.status_code == 200, f"Body: {response.text}"
    data = response.json()
    assert data["total_features"] == 1

    poly = next(
        (m for m in data["measurements"] if m["geometry_type"] == "Polygon"), None
    )
    assert poly is not None
    assert poly["measurement_type"] == "area"
    assert poly["measurement_value"] is not None
    assert poly["unit"] == "m²"


def test_get_summary():
    zip_path = create_polygon_shapefile_zip()
    with open(zip_path, "rb") as f:
        upload_resp = client.post(
            "/api/files/", files={"file": ("test.zip", f, "application/zip")}
        )
    file_id = upload_resp.json()["id"]

    response = client.get(f"/api/files/{file_id}/summary/")
    assert response.status_code == 200, f"Body: {response.text}"
    data = response.json()
    assert data["file_id"] == file_id
    assert data["polygon_count"] == 1
    assert data["total_area_m2"] > 0
