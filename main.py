from contextlib import asynccontextmanager
from asyncio import create_task

from config import PORT, DB_PATH, SENTRY_API_KEY, PRODUCTION_MODE
from _websockets import websocket_router
from db.cache.dict import DiskCacheDB, VectorStore
from db._appwrite.db_register import prepare_database, WaitList
from api.auth.services import hash_email
from api.product.deep_search import initialize_list_tools

from api import (
    chat_router, 
    auth_router, 
    product_router, 
    track_router, 
    queue_worker, 
    payment_router, 
    admin_router
)

from utils.logging import logger
from utils.queue import PRIORITY_LEVELS
from utils.middleware import AuthenticationMiddleware
from utils._craw4ai import CrawlerManager
from utils.background import background_task
from utils.request_session import http_client
# from utils.emails import send_waitlist_email
from utils.exceptions import PaymentRequiredError
from utils.exceptions_handlers import validation_exception_handler, payment_exception_handler

import uvicorn
import sentry_sdk
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

        # Initialize list_tools for deep search
        logger.info("Initializing list tools for deep search...")
        await initialize_list_tools()
        
        db_cache = DiskCacheDB(cache_dir=str(DB_PATH))

        await db_cache.initialize()
        logger.info("Database manager initialized successfully")
        
        logger.info("Initializing HTTP client...")
        http_client.initialize()

        logger.info("HTTP client initialized successfully")
        
        store = VectorStore()
        logger.info("Initializing vector store...")
        await store.initialize()
        logger.info("Initializing web crawler...")
        await CrawlerManager.initialize(use_tor=True if PRODUCTION_MODE == 'true' else False)
        logger.info("Web crawler initialization completed.")
        stats = await db_cache.get_stats()
        logger.info(f"Initial cache stats: {stats}")

        for level in range(PRIORITY_LEVELS):
            create_task(queue_worker(level))
    
        
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


app.add_middleware(AuthenticationMiddleware)

app.include_router(chat_router, prefix="/api/chats", tags=["Chat"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(product_router, prefix="/api/product", tags=["Product"])
app.include_router(websocket_router, prefix="/websocket", tags=["WebSocket"])
app.include_router(track_router, prefix="/api/track", tags=["Track"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(payment_router, prefix="/api/payments", tags=["Payment"])

app.router.lifespan_context = lifespan

# Make db_manager available to request state
@app.middleware("http")
async def add_db_manager(request: Request, call_next):
    """Add database manager to request state."""
    request.state.db_cache = db_cache
    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "INTERNAL SERVER ERROR", "error": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(PaymentRequiredError)
async def payment_exception(request: Request, exc: PaymentRequiredError):
    return await payment_exception_handler(request, exc)

# sentry_sdk.init(
#     dsn=SENTRY_API_KEY,
#     # Add data like request headers and IP for users,
#     # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
#     send_default_pii=True,
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for tracing.
#     traces_sample_rate=1.0,
#     _experiments={
#         # Set continuous_profiling_auto_start to True
#         # to automatically start the profiler on when
#         # possible.
#         "continuous_profiling_auto_start": True,
#     },
# )

if __name__ == "__main__":
    # from installer import ensure_playwright_installed
    # ensure_playwright_installed()

    logger.info("Starting FastAPI server.")
    uvicorn.run(app, port=int(PORT))  # Ensure PORT is an integer