import asyncio
import websockets

from gimbalcmd import GimbalControl
from infer import automated

clients = set()

gc = GimbalControl()

mode = 'manual'

mode_event = asyncio.Event()

async def handle_connection(websocket):
    global mode, mode_event
    clients.add(websocket)
    try:
        mode_event.set()
        await automated(embedded=True, event=mode_event, clients=clients)
        async for message in websocket:
            print('message', message)
            if mode == 'manual':
                if message != 'auto':
                    gc.handle_manual(message)
                else:
                    print('Switching to auto')
                    mode = 'auto'
                    mode_event.set()
            elif message == 'manual':
                mode_event.clear()
                mode = 'manual'
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        pass
        
async def main():
    # server = await websockets.serve(handle_connection, "localhost", 8765)
    # await asyncio.gather(server.wait_closed(), automated(embedded=True, event=mode_event, clients=clients))
    # video_task = asyncio.create_task(automated(embedded=True, event=mode_event, clients=clients))
    # await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running

asyncio.run(main())
