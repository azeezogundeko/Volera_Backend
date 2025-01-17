import asyncio
from contextlib import asynccontextmanager

from api import chat_router, auth_router, product_router, track_router
from db._appwrite.db_register import prepare_database
from _websockets import websocket_router
from utils.logging import logger
from utils._craw4ai import CrawlerManager
from config import PORT, DB_PATH
from utils.db_manager import ProductDBManager
from utils.exceptions_handlers import validation_exception_handler
from utils.request_session import http_client
from utils.background import background_task

import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Global database manager instance
db_manager: ProductDBManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the FastAPI application.
    This ensures proper initialization and cleanup of resources.
    """
    # Initialize database manager on startup
    global db_manager
    try:
        logger.info("Preparing database...")
        await prepare_database()
        logger.info("Database preparation completed.")
        logger.info("Initializing database manager...")
        db_manager = ProductDBManager(
            db_path=str(DB_PATH),
            cleanup_interval=3600,  # 1 hour cleanup interval
            max_workers=4
        )
        logger.info("Database manager initialized successfully")

        logger.info("Initializing HTTP client...")
        try:
            http_client.initialize()
        except Exception as e:
            logger.error(str(e))

        logger.info("HTTP client initialized successfully")
        
        logger.info("Initializing web crawler...")
        await CrawlerManager.initialize()
        logger.info("Web crawler initialization completed.")
        stats = await db_manager.get_cache_stats()
        logger.info(f"Initial cache stats: {stats}")
        
        yield
        
    finally:
        # Shutdown logic
        logger.info("Application is shutting down...")
        await http_client.close()
        logger.info("HTTP client cleaned up successfully")
        logger.info("Cleaning up web crawler...")
        await CrawlerManager.cleanup()
        logger.info("Web crawler cleanup completed.")

        await background_task.close()
        logger.info("Background task closed successfully")
        if db_manager:
            logger.info("Cleaning up database manager...")
            await db_manager.close()
            logger.info("Database manager cleaned up successfully")

# app = FastAPI()
app = FastAPI(lifespan=lifespan)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
    request.state.db_manager = db_manager
    response = await call_next(request)
    return response

@app.middleware("websocket")
async def add_db_manager_ws(websocket: WebSocket, call_next):
    """Add database manager to WebSocket state."""
    # await websocket.accept()
    websocket.state.db_manager = db_manager
    response = await call_next(websocket)
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
    
if __name__ == "__main__":
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, port=int(PORT))  # Ensure PORT is an integer