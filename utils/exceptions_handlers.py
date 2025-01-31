from fastapi.exceptions import RequestValidationError
from fastapi import status
from fastapi.responses import JSONResponse
from .exceptions import PaymentRequiredError

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
                "message":"Bad Request"  # Convert ValueError to string
            }
        )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )


async def payment_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={"message": str(exc), "error": str(exc)},
    )

    # if isinstance(exc, PaymentRequiredError):