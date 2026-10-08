
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from app.core.exceptions import UnsupportedFileTypeError
from app.db import repository
from app.models.schemas import (
    FileFeaturesResponse,
    FileInfoResponse,
    FileUploadResponse,
    ProcessedFileRecord,
)
from app.services.geo_reader import read_geospatial_file


CHUNK_SIZE_BYTES = 1024 * 1024


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_upload_file(upload_file: UploadFile) -> None:
    extension = get_file_extension(upload_file.filename or "")

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or 'unknown'}'. Allowed types: {allowed}."
        )


async def save_upload_file(upload_file: UploadFile) -> FileUploadResponse:
    validate_upload_file(upload_file)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_id = uuid4().hex
    original_filename = Path(upload_file.filename or "upload").name
    extension = get_file_extension(original_filename)
    stored_filename = f"{file_id}{extension}"
    destination = UPLOAD_DIR / stored_filename

    file_size = 0
    with destination.open("wb") as buffer:
        while chunk := await upload_file.read(CHUNK_SIZE_BYTES):
            file_size += len(chunk)
            buffer.write(chunk)

    read_result = read_geospatial_file(destination)
    uploaded_at = datetime.now(timezone.utc)

    record = ProcessedFileRecord(
        id=file_id,
        filename=original_filename,
        stored_filename=stored_filename,
        content_type=upload_file.content_type,
        file_size_bytes=file_size,
        feature_count=read_result.feature_count,
        crs=read_result.crs,
        status="COMPLETED",
        uploaded_at=uploaded_at,
        features=read_result.features,
    )
    repository.save_processed_file(record)

    return FileUploadResponse(
        id=file_id,
        filename=original_filename,
        stored_filename=stored_filename,
        content_type=upload_file.content_type,
        file_size_bytes=file_size,
        feature_count=read_result.feature_count,
        crs=read_result.crs,
        status="COMPLETED",
        uploaded_at=uploaded_at,
        message="File uploaded and processed successfully.",
    )


def get_file_info(file_id: str) -> FileInfoResponse:
    record = repository.get_processed_file(file_id)

    return FileInfoResponse(
        id=record.id,
        filename=record.filename,
        stored_filename=record.stored_filename,
        feature_count=record.feature_count,
        crs=record.crs,
        status=record.status,
        uploaded_at=record.uploaded_at,
    )


def get_file_features(file_id: str) -> FileFeaturesResponse:
    record = repository.get_processed_file(file_id)

    return FileFeaturesResponse(
        id=record.id,
        filename=record.filename,
        feature_count=record.feature_count,
        crs=record.crs,
        features=record.features,
    )
