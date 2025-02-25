from fastapi.exceptions import RequestValidationError
from fastapi import status
from fastapi.responses import JSONResponse
from .exceptions import PaymentRequiredError

async def validation_exception_handler(request, exc):
    if isinstance(exc, RequestValidationError):
        error_messages = []
        for error in exc.errors():
            error_dict = {
                "loc": " -> ".join(str(loc) for loc in error.get("loc", [])),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            }
            error_messages.append(error_dict)
            
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation error",
                "errors": error_messages
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


async def payment_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={"message": str(exc), "error": str(exc)},
    )

    # if isinstance(exc, PaymentRequiredError):