from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from api.auth.services import get_current_user  # Ensure this function correctly verifies tokens

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # ✅ Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            token = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]  # Extract the actual token
            
            if not token:
                raise Exception("No token provided")

            # ✅ Fetch authenticated user using the extracted token
            user = await get_current_user(token)

            # ✅ Attach the user to request.state
            request.state.user = user

        except Exception as e:
            # Handle authentication failure (user is not authenticated)
            request.state.user = None

        # Continue processing request
        response = await call_next(request)
        return response
