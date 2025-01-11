import asyncio
from contextlib import asynccontextmanager

from api import chat_router, auth_router, product_router
from db._appwrite.db_register import prepare_database
from _websockets import websocket_router
from utils.logging import logger
from utils._craw4ai import CrawlerManager
from config import PORT, DB_PATH
from utils.db_manager import ProductDBManager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
        
        logger.info("Initializing web crawler...")
        await CrawlerManager.initialize()
        logger.info("Web crawler initialization completed.")
        stats = await db_manager.get_cache_stats()
        logger.info(f"Initial cache stats: {stats}")
        
        yield
        
    finally:
        # Shutdown logic
        logger.info("Application is shutting down...")
        await CrawlerManager.cleanup()
        logger.info("Web crawler cleanup completed.")
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

app.router.lifespan_context = lifespan

# Make db_manager available to request state
@app.middleware("http")
async def add_db_manager(request: Request, call_next):
    """Add database manager to request state."""
    request.state.db_manager = db_manager
    response = await call_next(request)
    return response

# Example of how to use db_manager in a route
@app.get("/cache/stats")
async def get_cache_stats():
    """Get current cache statistics."""
    if not db_manager:
        return {"error": "Database manager not initialized"}
    return await db_manager.get_cache_stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached data."""
    if not db_manager:
        return {"error": "Database manager not initialized"}
    await db_manager.clear_cache()
    return {"message": "Cache cleared successfully"}

@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "INTERNAL SERVER ERROR", "error": str(exc)},
    )
    
if __name__ == "__main__":
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, port=int(PORT))  # Ensure PORT is an integer