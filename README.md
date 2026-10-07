# Aereo Geospatial File Measurement API v2.0

Production-grade FastAPI backend service for geospatial file processing — accepts Shapefile/KML uploads, extracts features, computes area/length measurements with proper CRS handling.

Built for the Aereo SDE Internship assessment.

## Setup

```bash
git clone https://github.com/Koushik926/aereo-geospatial-api.git
cd aereo-geospatial-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Interactive docs: `http://localhost:8000/docs`

## Docker

```bash
cd deploy && docker-compose up --build
```

## CI/CD

GitHub Actions runs on every push:
- Lint (ruff, black, mypy)
- Security scan (bandit, safety)
- Tests with coverage (pytest-cov)

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /api/files/ | Upload .zip (shapefile) or .kml |
| GET | /api/files/{id}/ | File metadata (id, filename, feature_count, crs, status) |
| GET | /api/files/{id}/measurements/ | Per-feature measurements |
| GET | /api/files/{id}/summary/ | Aggregate area/length totals |
| GET | /health | Health check |

## Architecture

```
app/
├── main.py                  # FastAPI app + lifespan
├── routes/files.py          # API endpoints
├── services/file_processor.py  # Core parsing & measurement logic
├── models/schemas.py        # Pydantic request/response schemas
├── models/                  # (reserved for future ORM expansion)
├── db/
│   ├── base.py              # SQLAlchemy engine + session
│   └── models.py            # ORM models
├── utils/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── crs.py               # CRS selection & transformation
│   ├── logging.py           # Structured JSON logging
│   └── __init__.py
├── middleware/
│   └── logging_middleware.py  # Request logging
└── __init__.py
```

### File-processing flow
1. File received → saved to temp dir
2. If `.zip` → extract → find `.shp` → read with fiona
3. If `.kml` → parse with ElementTree + shapely
4. Extract geometry type, CRS, properties per feature

### Measurement calculation
1. Detect if CRS is geographic → transform to UTM by centroid
2. Polygon → area (m²), LineString → length (m)
3. Point → no measurement (gracefully skipped)

### CRS handling
- Geographic (EPSG:4326) → UTM zone from centroid
- Polar regions → Web Mercator (EPSG:3857)
- Already projected → computed directly

## Design Decisions

| Decision | Rationale | Alternative |
|---|---|---|
| FastAPI | Async, auto-docs, validation | Django+DRF — more boilerplate |
| fiona+shapely+pyproj | Industry standard geospatial | GDAL bindings — complex API |
| ElementTree for KML | Reliable, no driver issues | fastkml — driver issues in this build |
| SQLite dev | Zero config | PostGIS — production use |
| UTM from centroid | Simple, accurate regionally | Predefined grid — overkill |
| Modular services layer | Testable, separable concerns | Monolithic — harder to maintain |
| Structured JSON logging | Production observability | Print statements — not scalable |

## Testing

```bash
pytest tests/ -v --cov=app
```

Covers: upload shapefile zip, upload KML, invalid extension, no file, file info, measurements, summary, unsupported geometry, empty KML.

## Learning & Future Scope

**Learned:** Geospatial parsing, CRS transforms, FastAPI architecture, structured logging, Docker, CI/CD, SQLAlchemy ORM.

**Future scope:**
- Background jobs (Celery + Redis) for large files
- Cloud storage (S3/GCS) for uploaded files
- PostGIS for spatial queries and indexing
- GeoJSON, GML support
- Multi-file batch uploads
- React dashboard for visualization
- Authentication & user management
- Rate limiting, file size validation
- Docker Swarm / Kubernetes deployment
