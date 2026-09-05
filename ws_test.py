import asyncio
import websockets

async def test():
    ws = await websockets.connect("ws://127.0.0.1:8001/ws")
    print("CONNECTED")
    print(await ws.recv())
    await ws.close()

asyncio.run(test())
