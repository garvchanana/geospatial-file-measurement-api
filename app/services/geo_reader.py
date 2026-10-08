
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from app.core.exceptions import FileProcessingError, MissingShapefileError, UnsupportedFileTypeError
from app.models.schemas import FeatureInfo, GeospatialReadResult


def read_geospatial_file(file_path: str | Path) -> GeospatialReadResult:
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".kml":
        geo_dataframe = _read_kml(file_path)
    elif extension == ".zip":
        geo_dataframe = _read_zipped_shapefile(file_path)
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type '{extension or 'unknown'}'.")

    return _to_read_result(file_path.name, geo_dataframe)


def _read_kml(file_path: Path) -> gpd.GeoDataFrame:
    try:
        geo_dataframe = gpd.read_file(file_path)
    except Exception as exc:
        raise FileProcessingError(f"Unable to read KML file: {exc}") from exc

    if geo_dataframe.crs is None:
        geo_dataframe = geo_dataframe.set_crs("EPSG:4326", allow_override=True)

    return geo_dataframe


def _read_zipped_shapefile(file_path: Path) -> gpd.GeoDataFrame:
    try:
        with TemporaryDirectory() as temp_dir:
            extract_dir = Path(temp_dir)
            with ZipFile(file_path) as archive:
                _validate_zip_members(archive)
                archive.extractall(extract_dir)

            shapefile_path = _find_shapefile(extract_dir)

            try:
                return gpd.read_file(shapefile_path)
            except Exception as exc:
                raise FileProcessingError(f"Unable to read Shapefile from ZIP: {exc}") from exc
    except BadZipFile as exc:
        raise FileProcessingError("Uploaded ZIP file is not a valid ZIP archive.") from exc


def _validate_zip_members(archive: ZipFile) -> None:
    for member_name in archive.namelist():
        member_path = Path(member_name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise FileProcessingError("ZIP archive contains an unsafe file path.")


def _find_shapefile(directory: Path) -> Path:
    shapefiles = sorted(directory.rglob("*.shp"))
    if not shapefiles:
        raise MissingShapefileError("ZIP archive does not contain a .shp file.")

    return shapefiles[0]


def _to_read_result(filename: str, geo_dataframe: gpd.GeoDataFrame) -> GeospatialReadResult:
    crs = _crs_to_string(geo_dataframe)
    features = [
        _to_feature_info(index=feature_index, row=row, crs=crs)
        for feature_index, (_, row) in enumerate(geo_dataframe.iterrows())
    ]

    return GeospatialReadResult(
        filename=filename,
        feature_count=len(features),
        crs=crs,
        features=features,
    )


def _to_feature_info(index: int, row: pd.Series, crs: str | None) -> FeatureInfo:
    geometry = row.geometry
    properties = {
        column: _clean_property_value(value)
        for column, value in row.drop(labels=["geometry"]).items()
    }

    return FeatureInfo(
        index=int(index),
        geometry_type=None if geometry is None else geometry.geom_type,
        geometry=None if geometry is None else mapping(geometry),
        crs=crs,
        properties=properties,
    )


def _crs_to_string(geo_dataframe: gpd.GeoDataFrame) -> str | None:
    if geo_dataframe.crs is None:
        return None

    return geo_dataframe.crs.to_string()


def _clean_property_value(value: object) -> object:
    if value is None:
        return None

    try:
        is_missing = pd.isna(value)
    except TypeError:
        is_missing = False

    if isinstance(is_missing, bool) and is_missing:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value
