from fastapi import FastAPI

from app.api.routes import files

app = FastAPI(
    title="Geospatial File Measurement API",
    version="0.1.0",
    description="Upload KML files or zipped Shapefiles and calculate geospatial measurements.",
)

app.include_router(files.router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
