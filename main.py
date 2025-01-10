from contextlib import asynccontextmanager

from api import chat_router, auth_router, product_router
from db._appwrite.db_register import prepare_database
from _websockets import websocket_router
from utils.logging import logger
from utils._craw4ai import CrawlerManager
from config import PORT

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Preparing database...")
        await prepare_database()
        logger.info("Database preparation completed.")
        
        logger.info("Initializing web crawler...")
        await CrawlerManager.initialize()
        logger.info("Web crawler initialization completed.")
        
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown logic
        logger.info("Application is shutting down...")
        await CrawlerManager.cleanup()
        logger.info("Web crawler cleanup completed.")

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

@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "INTERNAL SERVER ERROR", "error": str(exc)},
    )
    
if __name__ == "__main__":
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, port=int(PORT))  # Ensure PORT is an integer