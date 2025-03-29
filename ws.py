import asyncio
import websockets

from gimbalcmd import GimbalControl
from infer import automated

clients = set()

gc = GimbalControl()

mode = 'manual'

event = asyncio.Event()

async def handle_connection(websocket):
    global mode, event
    clients.add(websocket)
    try:
        await automated(embedded=True, event=event, ws=websocket)
        # async for message in websocket:
        #     if mode == 'manual':
        #         if message != 'auto':
        #             gc.handle_manual(message)
        #         else:
        #             print('Switching to auto')
        #             mode = 'auto'
        #             event.clear()
        #             await automated(embedded=True, event=event, ws=websocket)
        #     elif message == 'manual':
        #         event.set()
        #         mode = 'manual'
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        pass
        
async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running

asyncio.run(main())
