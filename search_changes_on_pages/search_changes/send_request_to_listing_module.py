import asyncio
import json
# from handle_price.utils import logger


async def send_command(command):
    try:
        reader, writer = await asyncio.open_connection('localhost', 12350)
        writer.write(json.dumps(command).encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()  # Ensure the connection is properly closed
    except (ConnectionRefusedError, OSError) as e:
        # logger.exception(f"Failed to send command to listing module. Error: {e}")
        pass


async def main_send_command(command):
    await send_command(command)
