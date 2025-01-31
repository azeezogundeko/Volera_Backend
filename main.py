from contextlib import asynccontextmanager

from config import PORT, DB_PATH
from _websockets import websocket_router
from db.cache.dict import DiskCacheDB, VectorStore
from db._appwrite.db_register import prepare_database, WaitList
from api.auth.services import get_current_user, hash_email
from api import chat_router, auth_router, product_router, track_router

from utils.logging import logger
from utils._craw4ai import CrawlerManager
from utils.background import background_task
from utils.request_session import http_client
from utils.emails import send_waitlist_email
from utils.exceptions_handlers import validation_exception_handler

import uvicorn
from fastapi import FastAPI, Request, Body
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.authentication import AuthenticationMiddleware

# Global database manager instance
# db_manager: ProductDBManager = None
db_cache: DiskCacheDB = None
store: VectorStore = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the FastAPI application.
    This ensures proper initialization and cleanup of resources.
    """
    global db_cache
    global store
    try:
        logger.info("Preparing database...")
        await prepare_database()
        logger.info("Database preparation completed.")
        logger.info("Initializing database manager...")

        db_cache = DiskCacheDB(cache_dir=str(DB_PATH))

        await db_cache.initialize()
        logger.info("Database manager initialized successfully")
        
        logger.info("Initializing HTTP client...")
        http_client.initialize()

        logger.info("HTTP client initialized successfully")
        
        logger.info("Initializing web crawler...")
        await CrawlerManager.initialize()
        logger.info("Web crawler initialization completed.")
        store = VectorStore()
        logger.info("Initializing vector store...")
        await store.initialize()
        stats = await db_cache.get_stats()
        logger.info(f"Initial cache stats: {stats}")
        
        yield
        
    finally:
        logger.info("Application is shutting down...")
        await http_client.close()
        logger.info("HTTP client cleaned up successfully")
        logger.info("Cleaning up web crawler...")
        await CrawlerManager.cleanup()
        logger.info("Web crawler cleanup completed.")

        await background_task.close()
        logger.info("Background task closed successfully")

        db_cache.close()
        logger.info("Database manager closed successfully")



app = FastAPI(lifespan=lifespan)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# app.add_middleware(AuthenticationMiddleware)

app.include_router(chat_router, prefix="/api/chats", tags=["chat"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(product_router, prefix="/api/product", tags=["product"])
app.include_router(websocket_router, prefix="/websocket", tags=["WebSocket"])
app.include_router(track_router, prefix="/api/track", tags=["track"])

app.router.lifespan_context = lifespan

# Make db_manager available to request state
@app.middleware("http")
async def add_db_manager(request: Request, call_next):
    """Add database manager to request state."""
    request.state.db_cache = db_cache
    response = await call_next(request)
    return response

@app.post("/api/waitlist")
async def save_waitlist(b: BackgroundTasks, email: str = Body()): 
    user_id = hash_email(email)
    await WaitList.get_or_create(user_id, {"email": email})
    b.add_task(send_waitlist_email, email)
    return {"message": "success", "data": email}

# @app.middleware("http")
# async def authenticate(request: Request, call_next):
#     """Add database manager to request state."""
#     auth_header = request.headers.get("Authorization")
    
#     if auth_header:
#         token = auth_header.split(" ")[1]  # Extract the token part from "Bearer <token>"
#         print(token)
#         request.user = await get_current_user(token)  # Pass the token to your auth function
        
#         if request.user is None:
#             raise HTTPException(status_code=401, detail="User not found")
#     else:
#         raise HTTPException(status_code=401, detail="User not found")
#         # request.user = None  

#     response = await call_next(request)
#     return response




@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "INTERNAL SERVER ERROR", "error": str(exc)},
    )



@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)
    
if __name__ == "__main__":
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, port=int(PORT))  # Ensure PORT is an integer