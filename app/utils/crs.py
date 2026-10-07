"""CRS utilities — select projected CRS and transform geometries."""

from pyproj import CRS, Transformer
from typing import Optional


def select_projected_crs(longitude: float, latitude: float) -> str:
    """Pick UTM zone EPSG code from lon/lat. Falls back to Web Mercator for poles."""
    if -80 <= latitude <= 84:
        zone = int((longitude + 180) / 6) + 1
        hemisphere = "north" if latitude >= 0 else "south"
        return f"EPSG:326{zone:02d}" if hemisphere == "north" else f"EPSG:327{zone:02d}"
    return "EPSG:3857"


def get_transformer(src_crs: str, dst_crs: str) -> Transformer:
    return Transformer.from_crs(
        CRS.from_user_input(src_crs), CRS.from_user_input(dst_crs), always_xy=True
    )


def normalize_crs(crs_input) -> Optional[str]:
    """Convert CRS to EPSG string."""
    if crs_input is None:
        return None
    try:
        authority = CRS.from_user_input(crs_input).to_authority()
        if authority:
            return f"{authority[0]}:{authority[1]}"
    except Exception:
        pass
    return str(crs_input)
