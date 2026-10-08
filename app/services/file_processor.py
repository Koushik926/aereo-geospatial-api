"""Core file processing — parses shapefiles and KML, computes measurements."""

import defusedxml.ElementTree as DefusedET
import uuid
from pathlib import Path
from typing import Tuple

import fiona
from pyproj import CRS
from shapely.geometry import shape, Point as ShapelyPoint
from shapely.geometry import LineString as ShapelyLineString
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import mapping as geom_mapping
from shapely.ops import transform

from app.utils.crs import select_projected_crs, get_transformer, normalize_crs

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
MEASUREMENT_GEOMETRY_TYPES = {
    "Polygon",
    "MultiPolygon",
    "LineString",
    "MultiLineString",
}
AREA_UNITS = "m²"
LENGTH_UNITS = "m"


def _serialize_value(v):
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    if isinstance(v, (list, tuple)):
        return [_serialize_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _serialize_value(x) for k, x in v.items()}
    return str(v)


def _props_to_dict(props) -> dict:
    if props is None:
        return {}
    try:
        return {k: _serialize_value(v) for k, v in props.items()}
    except AttributeError:
        return {"value": str(props)}


def _compute_centroid(features: list) -> Tuple[float, float]:
    lons, lats = [], []
    for feat in features:
        geom = shape(feat["geometry"])
        c = geom.centroid
        lons.append(c.x)
        lats.append(c.y)
    if not lons:
        return 0.0, 0.0
    return sum(lons) / len(lons), sum(lats) / len(lats)


def _is_geographic(crs_dict) -> bool:
    if crs_dict is None:
        return True
    try:
        return CRS.from_user_input(crs_dict).is_geographic
    except Exception:
        return True


def _parse_kml_coordinates(coords_str: str):
    points = []
    for part in coords_str.strip().split():
        parts = part.split(",")
        if len(parts) >= 2:
            points.append((float(parts[0]), float(parts[1])))
    return points


def _kml_to_features(file_path: Path) -> list:
    """Parse KML with ElementTree + shapely."""
    tree = DefusedET.parse(str(file_path))
    root = tree.getroot()
    features = []
    for pm in root.findall(".//kml:Placemark", KML_NS):
        name_el = pm.find("kml:name", KML_NS)
        name = name_el.text if name_el is not None else ""

        pt = pm.find(".//kml:Point", KML_NS)
        if pt is not None:
            coords = pt.find("kml:coordinates", KML_NS)
            if coords is not None and coords.text:
                pts = _parse_kml_coordinates(coords.text)
                if pts:
                    features.append(
                        {
                            "geometry": geom_mapping(ShapelyPoint(pts[0])),
                            "properties": {"name": name},
                        }
                    )
            continue

        ls = pm.find(".//kml:LineString", KML_NS)
        if ls is not None:
            coords = ls.find("kml:coordinates", KML_NS)
            if coords is not None and coords.text:
                pts = _parse_kml_coordinates(coords.text)
                if len(pts) >= 2:
                    features.append(
                        {
                            "geometry": geom_mapping(ShapelyLineString(pts)),
                            "properties": {"name": name},
                        }
                    )
            continue

        poly = pm.find(".//kml:Polygon", KML_NS)
        if poly is not None:
            ring = poly.find(".//kml:LinearRing", KML_NS)
            coords_el = (
                ring.find("kml:coordinates", KML_NS) if ring is not None else None
            )
            if coords_el is not None and coords_el.text:
                pts = _parse_kml_coordinates(coords_el.text)
                if len(pts) >= 3:
                    features.append(
                        {
                            "geometry": geom_mapping(ShapelyPolygon(pts)),
                            "properties": {"name": name},
                        }
                    )
            continue

    return features


def _read_shapefile(file_path: Path) -> tuple:
    with fiona.open(str(file_path)) as src:
        crs = src.crs
        features = [
            {
                "geometry": feat["geometry"],
                "properties": dict(feat.get("properties", {}) or {}),
            }
            for feat in src
        ]
    return crs, features


def process_file(file_path: Path) -> dict:
    """Parse file, compute measurements, return structured dict."""
    file_id = str(uuid.uuid4())

    if file_path.suffix.lower() == ".kml":
        crs, raw_features = "EPSG:4326", _kml_to_features(file_path)
    else:
        crs, raw_features = _read_shapefile(file_path)

    crs_str = normalize_crs(crs)
    is_geographic = _is_geographic(crs)
    centroid = _compute_centroid(raw_features)
    projected_crs = (
        select_projected_crs(centroid[0], centroid[1]) if is_geographic else crs
    )
    transformer = get_transformer(crs, projected_crs) if is_geographic and crs else None

    measurements = []
    for idx, feat in enumerate(raw_features):
        geom = shape(feat["geometry"])
        geom_type = geom.geom_type

        m_type, m_value, unit = None, None, None

        if geom_type in MEASUREMENT_GEOMETRY_TYPES and transformer is not None and crs:
            projected = transform(transformer.transform, geom)
            if geom_type in ("Polygon", "MultiPolygon"):
                m_value, m_type, unit = projected.area, "area", AREA_UNITS
            elif geom_type in ("LineString", "MultiLineString"):
                m_value, m_type, unit = projected.length, "length", LENGTH_UNITS
        elif geom_type in ("Polygon", "MultiPolygon", "LineString", "MultiLineString"):
            if geom_type in ("Polygon", "MultiPolygon"):
                m_value, m_type, unit = geom.area, "area", AREA_UNITS
            elif geom_type in ("LineString", "MultiLineString"):
                m_value, m_type, unit = geom.length, "length", LENGTH_UNITS

        measurements.append(
            {
                "feature_index": idx,
                "geometry_type": geom_type,
                "measurement_type": m_type,
                "measurement_value": m_value,
                "unit": unit,
                "properties": _props_to_dict(feat.get("properties", {})),
            }
        )

    return {
        "id": file_id,
        "filename": file_path.name,
        "crs": crs_str,
        "feature_count": len(raw_features),
        "status": "COMPLETED",
        "measurements": measurements,
    }
