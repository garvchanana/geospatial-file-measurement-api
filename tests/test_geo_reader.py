from zipfile import ZipFile

import geopandas as gpd
import pytest
from shapely.geometry import LineString

from app.core.exceptions import FileProcessingError, MissingShapefileError
from app.services.geo_reader import read_geospatial_file


def test_read_kml_extracts_features():
    result = read_geospatial_file("tests/sample_data/sample.kml")

    assert result.filename == "sample.kml"
    assert result.feature_count == 1
    assert result.crs == "EPSG:4326"
    assert result.features[0].geometry_type == "Point"
    assert result.features[0].properties["Name"] == "Sample Point"


def test_read_zipped_shapefile_extracts_features(tmp_path):
    shape_dir = tmp_path / "shape"
    shape_dir.mkdir()
    shape_path = shape_dir / "roads.shp"
    zip_path = tmp_path / "roads.zip"

    geo_dataframe = gpd.GeoDataFrame(
        [{"name": "Main Road", "geometry": LineString([(77.5946, 12.9716), (77.6, 12.98)])}],
        crs="EPSG:4326",
    )
    geo_dataframe.to_file(shape_path)

    with ZipFile(zip_path, "w") as archive:
        for path in shape_dir.iterdir():
            archive.write(path, arcname=path.name)

    result = read_geospatial_file(zip_path)

    assert result.filename == "roads.zip"
    assert result.feature_count == 1
    assert result.crs == "EPSG:4326"
    assert result.features[0].geometry_type == "LineString"
    assert result.features[0].properties["name"] == "Main Road"


def test_read_zip_without_shapefile_raises_clear_error(tmp_path):
    zip_path = tmp_path / "empty.zip"

    with ZipFile(zip_path, "w") as archive:
        archive.writestr("notes.txt", "not a shapefile")

    with pytest.raises(MissingShapefileError, match="does not contain a .shp"):
        read_geospatial_file(zip_path)


def test_read_unsafe_zip_raises_clear_error(tmp_path):
    zip_path = tmp_path / "unsafe.zip"

    with ZipFile(zip_path, "w") as archive:
        archive.writestr("../bad.shp", "unsafe")

    with pytest.raises(FileProcessingError, match="unsafe file path"):
        read_geospatial_file(zip_path)
