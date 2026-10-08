from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.exceptions import FileProcessingError, FileRecordNotFoundError, UnsupportedFileTypeError
from app.models.schemas import (
    FileFeaturesResponse,
    FileInfoResponse,
    FileMeasurementsResponse,
    FileUploadResponse,
)
from app.services.file_service import get_file_features, get_file_info, save_upload_file
from app.services.measurement_service import get_file_measurements

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a geospatial file",
)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    try:
        return await save_upload_file(file)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except FileProcessingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/",
    response_model=FileInfoResponse,
    summary="Get uploaded file information",
)
def read_file_info(file_id: str) -> FileInfoResponse:
    try:
        return get_file_info(file_id)
    except FileRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/features/",
    response_model=FileFeaturesResponse,
    summary="Get extracted features for an uploaded file",
)
def read_file_features(file_id: str) -> FileFeaturesResponse:
    try:
        return get_file_features(file_id)
    except FileRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/measurements/",
    response_model=FileMeasurementsResponse,
    summary="Get feature measurements for an uploaded file",
)
def read_file_measurements(file_id: str) -> FileMeasurementsResponse:
    try:
        return get_file_measurements(file_id)
    except FileRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
