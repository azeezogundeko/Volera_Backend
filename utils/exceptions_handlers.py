from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request


async def validation_exception_handler(request: Request, exc: RequestValidationError):
        print(request)
        return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "RequestValidationError",
            "message": exc.errors(),
        },
    )