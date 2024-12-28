from contextlib import asynccontextmanager

from api import chat_router
from db import prepare_database
from _websockets import websocket_router
from utils.logging import logger

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Preparing database...")
        await prepare_database()
        logger.info("Database preparation completed.")
        # await start_session_sync_task()
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown logic
        logger.info("Application is shutting down...")

# app = FastAPI()
app = FastAPI(lifespan=lifespan)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(chat_router, prefix="/api/chats", tags=["chat"])
app.include_router(websocket_router, prefix="/websocket", tags=["WebSocket"])

app.router.lifespan_context = lifespan



if __name__ == "__main__":
    uvicorn.run(
            "main:app", 
            host="localhost", 
            port=8888, 
            reload=True,  # Enable auto-reload during development
            log_level="info"
        )