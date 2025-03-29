import asyncio
import websockets

from gimbalcmd import GimbalControl

clients = set()

gc = GimbalControl()

async def handle_connection(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            gc.handle(message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running

asyncio.run(main())
