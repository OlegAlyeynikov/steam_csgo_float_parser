import asyncio
import json
import os


async def send_command(command):
    try:
        reader, writer = await asyncio.open_connection('localhost', int(os.getenv("PORT_BUY_MODULE")))
        writer.write(json.dumps(command).encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()  # Ensure the connection is properly closed
    except (ConnectionRefusedError, OSError) as e:
        print(f"Failed to send command to buy module. Error: {e}")


async def main_send_command(command):
    await send_command(command)
