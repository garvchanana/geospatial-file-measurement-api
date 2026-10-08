
import json
from pathlib import Path

from app.core.config import PROCESSED_DIR
from app.core.exceptions import FileRecordNotFoundError
from app.models.schemas import ProcessedFileRecord


def save_processed_file(record: ProcessedFileRecord) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    record_path = _record_path(record.id)
    record_path.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def get_processed_file(file_id: str) -> ProcessedFileRecord:
    record_path = _record_path(file_id)

    if not record_path.exists():
        raise FileRecordNotFoundError(f"File record '{file_id}' was not found.")

    return ProcessedFileRecord.model_validate_json(record_path.read_text(encoding="utf-8"))


def _record_path(file_id: str) -> Path:
    return PROCESSED_DIR / f"{file_id}.json"
