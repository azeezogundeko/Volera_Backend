from typing import Optional

from .connection_manager import manager
from .message_handler import handle_message
from utils.websocket import send_images, MetadataWebsocket

from fastapi import WebSocket, WebSocketDisconnect, APIRouter

router = APIRouter()

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, path: Optional[str] = None):
    """
    WebSocket endpoint that uses the ConnectionManager to manage connections.

    Args:
        websocket (WebSocket): WebSocket connection instance.
        path (Optional[str]): Optional path query parameters.
    """
    await manager.connect(websocket)
    
    # Generate a unique user ID for this connection
    user_id = "engr_ogundeko"
    
    try:
        with open(r"C:\Users\Engr Ogundeko\Desktop\SolveByte\volera\backend\output.txt", "r") as f:
            data = f.read()
        while True:            
            dat = await websocket.receive_text()
            metadata = MetadataWebsocket(
                url="https://www.jumia.com.ng//infinix-note-40-6.78-8gb-ram-256gb-rom-android-14-green-351680578.html",
                img_url="https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/87/5086153/1.jpg?7405",
                title="example"
            )
            await send_images(websocket, [metadata] * 8)
            # await stream_final_response(websocket, data)
            from asyncio import sleep

            await websocket.send_json({"type":"message","content":data})
            # Start searching
            await sleep(2)
            await websocket.send_json({"type": "message", "content": "Starting search..."})
            await sleep(2)

            await websocket.send_json({"type": "progress", "progress": {"status": "searching", "searched": 1}})
            await sleep(2)
            # Update progress
            await websocket.send_json({"type": "progress", "progress": {"status": "searching", "searched": 5}})
            await sleep(2)
            # Move to scraping
            await websocket.send_json({"type": "progress", "progress": {"status": "scraping", "scraped": 2}})
            await sleep(2)
            # await sleep(2)
            # Complete search
            await websocket.send_json({"type": "search_complete", "totalSearched": 10, "totalScraped": 5})
            await sleep(2)
            # Send final message
            await websocket.send_json({"type": "message", "content": {"content": "Here's what I found..."}})

            # Handle the message using the message handler
            # await handle_message(data, websocket, user_id)
    
    except WebSocketDisconnect as e:
        print(str(e))
        manager.disconnect(websocket)
