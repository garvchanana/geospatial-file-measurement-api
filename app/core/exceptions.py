class GeoAPIError(Exception):
    """Base exception for expected application errors."""


class UnsupportedFileTypeError(GeoAPIError):
    """Raised when the uploaded file extension is not supported."""


class FileProcessingError(GeoAPIError):
    """Raised when a geospatial file cannot be processed."""


class MissingShapefileError(FileProcessingError):
    """Raised when a ZIP upload does not contain a .shp file."""


class FileRecordNotFoundError(GeoAPIError):
    """Raised when processed metadata for a file ID does not exist."""
