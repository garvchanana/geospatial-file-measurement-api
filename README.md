# Geospatial File Measurement API

Backend service built with FastAPI for uploading KML files or zipped Shapefiles, extracting geospatial features, and returning measurement information.

## Features

- Upload `.kml` files.
- Upload `.zip` archives containing Shapefiles.
- Extract feature index, geometry type, geometry, CRS, and properties.
- Store processed results as JSON.
- Return uploaded file information by ID.
- Return extracted feature data by ID.
- Calculate measurements for supported geometries.
- Reproject geographic CRS data before measuring.
- Handle unsupported geometry types gracefully.

## Setup

```powershell
cd "D:\Python\Data Science Projects\Assignment-GeospatialAPI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Run Locally

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

API docs:

```text
http://127.0.0.1:8001/docs
```

If port `8001` is blocked, use another port such as `8080`.

## Run Tests

```powershell
python -m pytest -q
```

Current result:

```text
15 passed
```

## API Endpoints

```http
GET /health
POST /api/files/
GET /api/files/{id}/
GET /api/files/{id}/features/
GET /api/files/{id}/measurements/
```

## Upload File

```http
POST /api/files/
Content-Type: multipart/form-data
```

Form field:

```text
file: .kml file or .zip containing a Shapefile
```

PowerShell example:

```powershell
$response = curl.exe -X POST "http://127.0.0.1:8001/api/files/" `
  -F "file=@D:\Python\Data Science Projects\Assignment-GeospatialAPI\tests\sample_data\sample_measurements.kml" | ConvertFrom-Json

$response
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample_measurements.kml",
  "stored_filename": "abc123.kml",
  "content_type": "application/octet-stream",
  "file_size_bytes": 882,
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "uploaded_at": "2026-10-08T10:00:00Z",
  "message": "File uploaded and processed successfully."
}
```

Use `curl.exe` instead of `Invoke-RestMethod -Form` for older Windows PowerShell versions.

## File Information

```http
GET /api/files/{id}/
```

PowerShell example:

```powershell
curl.exe "http://127.0.0.1:8001/api/files/$($response.id)/"
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample_measurements.kml",
  "stored_filename": "abc123.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "uploaded_at": "2026-10-08T10:00:00Z"
}
```

## Extracted Features

```http
GET /api/files/{id}/features/
```

PowerShell example:

```powershell
curl.exe "http://127.0.0.1:8001/api/files/$($response.id)/features/"
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample_measurements.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "features": [
    {
      "index": 0,
      "geometry_type": "Point",
      "geometry": {
        "type": "Point",
        "coordinates": [77.5946, 12.9716, 0.0]
      },
      "crs": "EPSG:4326",
      "properties": {
        "Name": "Sample Point"
      }
    }
  ]
}
```

## Measurements

```http
GET /api/files/{id}/measurements/
```

PowerShell example:

```powershell
curl.exe "http://127.0.0.1:8001/api/files/$($response.id)/measurements/"
```

Example response:

```json
{
  "id": "abc123",
  "filename": "sample_measurements.kml",
  "feature_count": 3,
  "source_crs": "EPSG:4326",
  "measurements": [
    {
      "feature_index": 0,
      "geometry_type": "Point",
      "measurement_type": null,
      "value": null,
      "unit": null,
      "source_crs": "EPSG:4326",
      "measurement_crs": null,
      "message": "Point geometries do not require measurement."
    },
    {
      "feature_index": 1,
      "geometry_type": "LineString",
      "measurement_type": "length",
      "value": 1085.604,
      "unit": "meters",
      "source_crs": "EPSG:4326",
      "measurement_crs": "EPSG:32643",
      "message": "Length calculated successfully."
    },
    {
      "feature_index": 2,
      "geometry_type": "Polygon",
      "measurement_type": "area",
      "value": 1201684.717,
      "unit": "square_meters",
      "source_crs": "EPSG:4326",
      "measurement_crs": "EPSG:32643",
      "message": "Area calculated successfully."
    }
  ]
}
```

## Architecture

```text
app/
  api/routes/          FastAPI route modules
  core/                settings and application exceptions
  db/                  JSON repository for processed files
  models/              Pydantic response and persistence schemas
  services/            upload, reading, CRS, and measurement logic
  storage/uploads/     uploaded source files
  storage/processed/   processed JSON records
tests/
  sample_data/         sample KML files
```

## File Processing Flow

1. Client uploads a `.kml` file or `.zip` archive.
2. The upload service validates the file extension.
3. The original file is saved under `app/storage/uploads/`.
4. The geospatial reader loads the file using GeoPandas.
5. ZIP uploads are safely extracted and scanned for a `.shp` file.
6. Each feature is normalized into index, geometry type, geometry, CRS, and properties.
7. The processed record is saved as JSON under `app/storage/processed/`.
8. API endpoints read from the processed JSON record.

## Measurement Flow

1. The measurement endpoint loads the processed file record.
2. Each stored GeoJSON-like geometry is converted back to a Shapely geometry.
3. Points return a clear no-measurement message.
4. Polygons and MultiPolygons return area in square meters.
5. LineStrings and MultiLineStrings return length in meters.
6. Unsupported geometries return a clear message instead of crashing.

## CRS Handling

The API does not calculate distance or area directly in latitude/longitude degrees.

If the source CRS is geographic, such as `EPSG:4326`, the service:

1. Gets a representative point for the feature.
2. Selects the matching UTM zone from longitude and hemisphere.
3. Reprojects the geometry with PyProj and Shapely.
4. Calculates area or length in the projected CRS.

For KML files with missing CRS metadata, the reader assumes `EPSG:4326`, which matches the KML standard expectation.

## Design Decisions

- FastAPI was selected for quick API development, validation, and built-in Swagger documentation.
- GeoPandas was used for reading KML and Shapefile data.
- Pyogrio was used instead of Fiona because it installs more reliably on modern Windows Python environments.
- JSON file storage was selected to keep the assignment simple and reviewable.
- UTM reprojection was selected dynamically per feature for practical local area and distance measurements.
- Unsupported geometries and missing CRS are handled as per-feature messages instead of failing the entire request.

## Learning

This project helped reinforce:

- handling geospatial uploads in a backend API
- reading KML and zipped Shapefile data
- separating API, storage, processing, CRS, and measurement logic
- avoiding incorrect measurements in geographic coordinate systems
- writing tests for geospatial processing and API behavior

## Future Scope

- Replace JSON storage with PostgreSQL/PostGIS.
- Add background processing for large uploads.
- Add authentication and upload ownership.
- Add file deletion and retention policies.
- Add support for GeoJSON and GPKG.
- Add richer validation for Shapefile component completeness.
- Add pagination for very large feature collections.
- Add Docker setup for easier deployment.
