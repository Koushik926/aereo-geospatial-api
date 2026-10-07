"""Test fixtures — create shapefile/KML test files."""

import tempfile
import zipfile
from pathlib import Path

import fiona
from shapely.geometry import Polygon, mapping


def create_polygon_shapefile_zip() -> Path:
    """Create a shapefile zip with a Polygon."""
    tmp_dir = Path(tempfile.mkdtemp())
    shp_path = tmp_dir / "polygons.shp"
    schema = {"geometry": "Polygon", "properties": {"name": "str"}}
    with fiona.open(
        str(shp_path), "w", driver="ESRI Shapefile", schema=schema, crs="EPSG:4326"
    ) as dst:
        dst.write(
            {
                "geometry": mapping(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])),
                "properties": {"name": "poly1"},
            }
        )

    zip_path = tmp_dir / "test.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        for f in tmp_dir.iterdir():
            if f.name != "test.zip":
                zf.write(f, f.name)
    return zip_path


def create_kml() -> Path:
    """Create a KML file with a Polygon."""
    tmp_dir = Path(tempfile.mkdtemp())
    kml_path = tmp_dir / "test.kml"
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon><outerBoundaryIs><LinearRing>
        <coordinates>0,0 1,0 1,1 0,1 0,0</coordinates>
      </LinearRing></outerBoundaryIs></Polygon>
    </Placemark>
  </Document>
</kml>"""
    kml_path.write_text(kml_content)
    return kml_path
