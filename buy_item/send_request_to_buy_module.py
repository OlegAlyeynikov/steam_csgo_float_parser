import asyncio
import json


async def send_command(command):
    try:
        reader, writer = await asyncio.open_connection('localhost', 12351)
        writer.write(json.dumps(command).encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()  # Ensure the connection is properly closed
    except (ConnectionRefusedError, OSError) as e:
        print(f"Failed to send command to buy module. Error: {e}")


async def main_send_command(command):
    await send_command(command)


if __name__ == "__main__":
    command = {
        "initial_link": "https://steamcommunity.com/market/listings/730/MAG-7%20%7C%20Heat%20(Minimal%20Wear)",
        'action': 'action',
        'market_name': "MAG-7 | Heat",
        'market_id': "4649471418285033823",
        'price': 76,
        'fee': 9,
        'float': 0.3,
        'pattern': 45

        # 'game': GameOptions.CS,  # This should be a string like 'CSGO'
        # 'currency': Currency.USD  # This should be a string like 'USD'
    }
    asyncio.run(main_send_command(command))
