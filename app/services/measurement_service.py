
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from app.db import repository
from app.models.schemas import FeatureInfo, FeatureMeasurement, FileMeasurementsResponse
from app.services.crs_service import choose_measurement_crs, parse_crs, project_geometry


AREA_GEOMETRIES = {"Polygon", "MultiPolygon"}
LENGTH_GEOMETRIES = {"LineString", "MultiLineString"}
POINT_GEOMETRIES = {"Point", "MultiPoint"}


def get_file_measurements(file_id: str) -> FileMeasurementsResponse:
    record = repository.get_processed_file(file_id)

    measurements = [
        calculate_feature_measurement(feature=feature, source_crs_value=record.crs)
        for feature in record.features
    ]

    return FileMeasurementsResponse(
        id=record.id,
        filename=record.filename,
        feature_count=record.feature_count,
        source_crs=record.crs,
        measurements=measurements,
    )


def calculate_feature_measurement(
    feature: FeatureInfo,
    source_crs_value: str | None,
) -> FeatureMeasurement:
    if feature.geometry is None or feature.geometry_type is None:
        return _unsupported(feature, source_crs_value, "Feature has no geometry.")

    geometry = shape(feature.geometry)

    if geometry.is_empty:
        return _unsupported(feature, source_crs_value, "Feature geometry is empty.")

    if feature.geometry_type in POINT_GEOMETRIES:
        return FeatureMeasurement(
            feature_index=feature.index,
            geometry_type=feature.geometry_type,
            measurement_type=None,
            value=None,
            unit=None,
            source_crs=source_crs_value,
            measurement_crs=None,
            message="Point geometries do not require measurement.",
        )

    if feature.geometry_type not in AREA_GEOMETRIES | LENGTH_GEOMETRIES:
        return _unsupported(
            feature,
            source_crs_value,
            f"Measurement is not supported for {feature.geometry_type}.",
        )

    source_crs = parse_crs(source_crs_value)
    if source_crs is None:
        return _unsupported(
            feature,
            source_crs_value,
            "Source CRS is missing, so measurement was skipped.",
        )

    measurement_crs = choose_measurement_crs(geometry, source_crs)
    projected_geometry = project_geometry(geometry, source_crs, measurement_crs)

    return _measure_projected_geometry(
        feature=feature,
        geometry=projected_geometry,
        source_crs_value=source_crs_value,
        measurement_crs_value=measurement_crs.to_string(),
    )


def _measure_projected_geometry(
    feature: FeatureInfo,
    geometry: BaseGeometry,
    source_crs_value: str | None,
    measurement_crs_value: str,
) -> FeatureMeasurement:
    if feature.geometry_type in AREA_GEOMETRIES:
        return FeatureMeasurement(
            feature_index=feature.index,
            geometry_type=feature.geometry_type,
            measurement_type="area",
            value=round(float(geometry.area), 3),
            unit="square_meters",
            source_crs=source_crs_value,
            measurement_crs=measurement_crs_value,
            message="Area calculated successfully.",
        )

    return FeatureMeasurement(
        feature_index=feature.index,
        geometry_type=feature.geometry_type,
        measurement_type="length",
        value=round(float(geometry.length), 3),
        unit="meters",
        source_crs=source_crs_value,
        measurement_crs=measurement_crs_value,
        message="Length calculated successfully.",
    )


def _unsupported(
    feature: FeatureInfo,
    source_crs_value: str | None,
    message: str,
) -> FeatureMeasurement:
    return FeatureMeasurement(
        feature_index=feature.index,
        geometry_type=feature.geometry_type,
        measurement_type=None,
        value=None,
        unit=None,
        source_crs=source_crs_value,
        measurement_crs=None,
        message=message,
    )
