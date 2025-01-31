from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def validation_exception_handler(request, exc):
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation error",
                "errors": exc.errors()
            }
        )
    elif isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(exc)  # Convert ValueError to string
            }
        )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )