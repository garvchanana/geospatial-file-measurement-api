from datetime import datetime, timezone

from fastapi.testclient import TestClient
from shapely.geometry import GeometryCollection, LineString, Point, Polygon, mapping

from app.db import repository
from app.main import app
from app.models.schemas import FeatureInfo, ProcessedFileRecord
from app.services.measurement_service import calculate_feature_measurement


client = TestClient(app)


def test_calculates_polygon_area_in_square_meters():
    feature = FeatureInfo(
        index=0,
        geometry_type="Polygon",
        geometry=mapping(
            Polygon(
                [
                    (77.5946, 12.9716),
                    (77.6046, 12.9716),
                    (77.6046, 12.9816),
                    (77.5946, 12.9816),
                    (77.5946, 12.9716),
                ]
            )
        ),
        crs="EPSG:4326",
        properties={},
    )

    measurement = calculate_feature_measurement(feature, "EPSG:4326")

    assert measurement.measurement_type == "area"
    assert measurement.unit == "square_meters"
    assert measurement.value > 1_000_000
    assert measurement.measurement_crs != "EPSG:4326"


def test_calculates_line_length_in_meters():
    feature = FeatureInfo(
        index=0,
        geometry_type="LineString",
        geometry=mapping(LineString([(77.5946, 12.9716), (77.6046, 12.9716)])),
        crs="EPSG:4326",
        properties={},
    )

    measurement = calculate_feature_measurement(feature, "EPSG:4326")

    assert measurement.measurement_type == "length"
    assert measurement.unit == "meters"
    assert measurement.value > 100
    assert measurement.measurement_crs != "EPSG:4326"


def test_point_returns_no_measurement():
    feature = FeatureInfo(
        index=0,
        geometry_type="Point",
        geometry=mapping(Point(77.5946, 12.9716)),
        crs="EPSG:4326",
        properties={},
    )

    measurement = calculate_feature_measurement(feature, "EPSG:4326")

    assert measurement.measurement_type is None
    assert measurement.value is None
    assert "do not require measurement" in measurement.message


def test_unsupported_geometry_returns_message_without_crashing():
    feature = FeatureInfo(
        index=0,
        geometry_type="GeometryCollection",
        geometry=mapping(GeometryCollection([Point(77.5946, 12.9716)])),
        crs="EPSG:4326",
        properties={},
    )

    measurement = calculate_feature_measurement(feature, "EPSG:4326")

    assert measurement.measurement_type is None
    assert measurement.value is None
    assert "not supported" in measurement.message


def test_missing_crs_skips_measurement():
    feature = FeatureInfo(
        index=0,
        geometry_type="LineString",
        geometry=mapping(LineString([(77.5946, 12.9716), (77.6046, 12.9716)])),
        crs=None,
        properties={},
    )

    measurement = calculate_feature_measurement(feature, None)

    assert measurement.measurement_type is None
    assert measurement.value is None
    assert "Source CRS is missing" in measurement.message


def test_measurements_endpoint_returns_saved_file_measurements(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "PROCESSED_DIR", tmp_path)

    file_id = "measurement-test"
    record = ProcessedFileRecord(
        id=file_id,
        filename="features.kml",
        stored_filename="features.kml",
        content_type="application/vnd.google-earth.kml+xml",
        file_size_bytes=100,
        feature_count=1,
        crs="EPSG:4326",
        status="COMPLETED",
        uploaded_at=datetime.now(timezone.utc),
        features=[
            FeatureInfo(
                index=0,
                geometry_type="LineString",
                geometry=mapping(LineString([(77.5946, 12.9716), (77.6046, 12.9716)])),
                crs="EPSG:4326",
                properties={"name": "Test line"},
            )
        ],
    )
    repository.save_processed_file(record)

    response = client.get(f"/api/files/{file_id}/measurements/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["feature_count"] == 1
    assert data["source_crs"] == "EPSG:4326"
    assert data["measurements"][0]["measurement_type"] == "length"
    assert data["measurements"][0]["unit"] == "meters"
