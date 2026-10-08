from pathlib import Path

from fastapi.testclient import TestClient

from app.db import repository
from app.main import app
from app.services import file_service


client = TestClient(app)
SAMPLE_KML_PATH = Path("tests/sample_data/sample.kml")


def test_upload_kml_file(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(file_service, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(repository, "PROCESSED_DIR", processed_dir)

    response = client.post(
        "/api/files/",
        files={
            "file": (
                "survey.kml",
                SAMPLE_KML_PATH.read_bytes(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "survey.kml"
    assert data["stored_filename"].endswith(".kml")
    assert data["file_size_bytes"] > 0
    assert data["feature_count"] == 1
    assert data["crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"
    assert (upload_dir / data["stored_filename"]).exists()
    assert (processed_dir / f"{data['id']}.json").exists()


def test_get_file_info_after_upload(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(file_service, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(repository, "PROCESSED_DIR", processed_dir)

    upload_response = client.post(
        "/api/files/",
        files={
            "file": (
                "survey.kml",
                SAMPLE_KML_PATH.read_bytes(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["filename"] == "survey.kml"
    assert data["feature_count"] == 1
    assert data["crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"


def test_get_file_features_after_upload(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(file_service, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(repository, "PROCESSED_DIR", processed_dir)

    upload_response = client.post(
        "/api/files/",
        files={
            "file": (
                "survey.kml",
                SAMPLE_KML_PATH.read_bytes(),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )
    file_id = upload_response.json()["id"]

    response = client.get(f"/api/files/{file_id}/features/")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == file_id
    assert data["feature_count"] == 1
    assert data["features"][0]["geometry_type"] == "Point"
    assert data["features"][0]["crs"] == "EPSG:4326"
    assert data["features"][0]["properties"]["Name"] == "Sample Point"


def test_get_file_info_returns_404_for_unknown_id(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "PROCESSED_DIR", tmp_path)

    response = client.get("/api/files/missing-id/")

    assert response.status_code == 404


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/files/",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
