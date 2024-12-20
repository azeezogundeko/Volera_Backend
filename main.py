from contextlib import asynccontextmanager

from api import chat_router
from db import prepare_database
from _websockets import websocket_router
from utils.logging import logger

import uvicorn
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Preparing database...")
        await prepare_database()
        logger.info("Database preparation completed.")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown logic
        logger.info("Application is shutting down...")

app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(websocket_router, prefix="/websocet", tags=["WebSocket"])



app.router.lifespan_context = lifespan



if __name__ == "__main__":
    uvicorn.run(
            "main:app", 
            host="localhost", 
            port=8888, 
            reload=True,  # Enable auto-reload during development
            log_level="info"
        )