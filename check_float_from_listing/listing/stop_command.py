import asyncio
import json

"""
This script creates a client that connects to server
(assuming it's running on 'localhost' with port 12343) and
sends the shutdown command = {"action": "stop"}.
"""


async def send_shutdown_command():
    reader, writer = await asyncio.open_connection('localhost', 12350)
    command = {"action": "stop"}
    writer.write(json.dumps(command).encode())
    await writer.drain()  # Ensure command is sent
    writer.close()
    await writer.wait_closed()
    print("Shutdown command sent.")


asyncio.run(send_shutdown_command())
