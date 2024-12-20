import websockets
import asyncio

async def test_websocket():
    try:
        # Replace with your actual WebSocket URL
        uri = "ws://localhost:8888/ws"  # Adjust port to match your configuration
        async with websockets.connect(uri) as websocket:
            # Send a test message
            await websocket.send("WebSocket Connection Test")
            
            # Wait for a response
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            return True
    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        return False

async def main():
    result = await test_websocket()
    print(f"WebSocket Connection Status: {'Active' if result else 'Inactive'}")

if __name__ == "__main__":
    asyncio.run(main())