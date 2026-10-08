
from pyproj import CRS, Transformer
from shapely import transform as shapely_transform
from shapely.geometry.base import BaseGeometry


def parse_crs(crs_value: str | None) -> CRS | None:
    if not crs_value:
        return None

    return CRS.from_user_input(crs_value)


def choose_measurement_crs(geometry: BaseGeometry, source_crs: CRS) -> CRS:
    if not source_crs.is_geographic:
        return source_crs

    lon, lat = _representative_lon_lat(geometry)
    zone = int((lon + 180) // 6) + 1
    zone = max(1, min(zone, 60))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone

    return CRS.from_epsg(epsg)


def project_geometry(
    geometry: BaseGeometry,
    source_crs: CRS,
    target_crs: CRS,
) -> BaseGeometry:
    if source_crs == target_crs:
        return geometry

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return shapely_transform(geometry, transformer.transform, interleaved=False)


def _representative_lon_lat(geometry: BaseGeometry) -> tuple[float, float]:
    representative_point = geometry.representative_point()
    return representative_point.x, representative_point.y
