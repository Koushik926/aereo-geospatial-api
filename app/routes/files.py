"""File API routes."""

import json
import tempfile
import zipfile
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models import UploadedFile, FeatureMeasurement
from app.services.file_processor import process_file
from app.models.schemas import (
    FileInfoResponse,
    MeasurementsResponse,
    MeasurementResponse,
    SummaryResponse,
)

router = APIRouter(prefix="/api/files", tags=["files"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=FileInfoResponse, status_code=201)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower() if file.filename else None
    if ext not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400, detail="Only .kml and .zip (shapefile) files accepted."
        )

    tmp_dir = Path(tempfile.mkdtemp())
    file_path = tmp_dir / (file.filename or "upload")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        if ext == ".zip":
            with zipfile.ZipFile(file_path, "r") as zf:
                shp_files = [n for n in zf.namelist() if n.lower().endswith(".shp")]
                if not shp_files:
                    raise HTTPException(status_code=400, detail="No .shp found in zip.")
                zf.extractall(tmp_dir)
                file_meta = process_file(tmp_dir / Path(shp_files[0]))
        else:
            file_meta = process_file(file_path)

        file_meta["filename"] = file.filename

        record = UploadedFile(
            id=file_meta["id"],
            filename=file_meta["filename"],
            feature_count=file_meta["feature_count"],
            crs=file_meta["crs"],
            status=file_meta["status"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        for idx, m in enumerate(file_meta["measurements"]):
            db.add(
                FeatureMeasurement(
                    file_id=record.id,
                    feature_index=idx,
                    geometry_type=m["geometry_type"],
                    measurement_type=m["measurement_type"],
                    measurement_value=m["measurement_value"],
                    unit=m["unit"],
                    properties=json.dumps(m["properties"]),
                )
            )
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return FileInfoResponse.model_validate(record)


@router.get("/{file_id}/", response_model=FileInfoResponse)
async def get_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileInfoResponse.model_validate(record)


@router.get("/{file_id}/measurements/", response_model=MeasurementsResponse)
async def get_measurements(file_id: str, db: Session = Depends(get_db)):
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")
    db_m = (
        db.query(FeatureMeasurement).filter(FeatureMeasurement.file_id == file_id).all()
    )
    measurements = [
        MeasurementResponse(
            feature_index=m.feature_index,
            geometry_type=m.geometry_type,
            measurement_type=m.measurement_type,
            measurement_value=m.measurement_value,
            unit=m.unit,
        )
        for m in db_m
    ]
    return MeasurementsResponse(
        file_id=file_id, total_features=len(measurements), measurements=measurements
    )


@router.get("/{file_id}/summary/", response_model=SummaryResponse)
async def get_summary(file_id: str, db: Session = Depends(get_db)):
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")
    db_m = (
        db.query(FeatureMeasurement).filter(FeatureMeasurement.file_id == file_id).all()
    )
    polygon_count = sum(
        1 for m in db_m if m.geometry_type in ("Polygon", "MultiPolygon")
    )
    linestring_count = sum(
        1 for m in db_m if m.geometry_type in ("LineString", "MultiLineString")
    )
    point_count = sum(1 for m in db_m if m.geometry_type == "Point")
    total_area = sum(
        (m.measurement_value or 0) for m in db_m if m.measurement_type == "area"
    )
    total_length = sum(
        (m.measurement_value or 0) for m in db_m if m.measurement_type == "length"
    )
    return SummaryResponse(
        file_id=file_id,
        total_features=len(db_m),
        polygon_count=polygon_count,
        linestring_count=linestring_count,
        point_count=point_count,
        total_area_m2=round(total_area, 4),
        total_length_m=round(total_length, 4),
    )
