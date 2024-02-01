import asyncio
import json
import os


async def send_command(command):
    try:
        reader, writer = await asyncio.open_connection('localhost', int(os.getenv("PORT_LISTING")))
        writer.write(json.dumps(command).encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()  # Ensure the connection is properly closed
    except (ConnectionRefusedError, OSError) as e:
        pass


async def main_send_command(command):
    await send_command(command)
