from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class ValidationError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details=details,
        )


class UnsupportedMediaTypeError(AppError):
    def __init__(self, filename: str, ext: str):
        super().__init__(
            message=f"File '{filename}' has unsupported extension '{ext}'",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="UNSUPPORTED_MEDIA_TYPE",
        )


class FileTooLargeError(AppError):
    def __init__(self, size: int, limit: int):
        super().__init__(
            message=f"File size ({size} bytes) exceeds limit ({limit} bytes)",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
        )


class ExtractionError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Document extraction error: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="EXTRACTION_ERROR",
            details=details,
        )


class ProviderError(AppError):
    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"{provider} provider error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="PROVIDER_ERROR",
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Standardized JSON response for application errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Standardized JSON response for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            }
        },
    )
