import asyncio
import datetime
import functools
import json
import signal
from urllib.parse import unquote, urlparse

from steampy.exceptions import ApiException
from steampy.models import GameOptions, Currency

from buy_module.globals import Shutdown_requested, set_shutdown_flag
from buy_module.utils import logger, send_async_request, write_to_csv, get_strings_length

count_success = 0
count_lock = asyncio.Lock()  # Lock for thread-safe counter increment
count_trying_buy_item = 0


def signal_handler(sig, frame, server_task):
    print("Received signal, stopping server...")
    server_task.cancel()


async def handle_client(reader, writer, steam_client_, server_):
    global count_success, count_trying_buy_item
    try:
        while not Shutdown_requested:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode()
            command = json.loads(message)
            if command.get("action") == "stop":
                set_shutdown_flag()
                logger.warning("Received command Stop")
                await steam_client_.cleanup()  # Close all sessions
                server_.close()
                await server_.wait_closed()
                logger.info("Server closed")
                writer.close()
                break
            elif command.get("action") == "action":
                logger.info(f'Received command to buy item !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                balance = steam_client_.steam_client.get_wallet_balance()
                logger.info(f"Balance: {balance}")
                price = command.get("price")
                logger.info(f"Purchasing price: {price}")
                if balance >= price / 100:
                    print(datetime.datetime.utcnow())
                    initial_link = command.get("initial_link")
                    print(initial_link)
                    parsed_url = urlparse(initial_link)
                    path = parsed_url.path
                    item_name = unquote(path.split('/')[-1])
                    float_value = command.get("float")
                    print(f"Float value: {float_value}")
                    pattern = command.get("pattern")
                    print(f"Pattern value: {pattern}")
                    price = command.get("price")
                    fee = command.get("fee")
                    print(f"Price: {price + fee}")
                    del command["action"]
                    del command["float"]
                    del command["pattern"]
                    del command["initial_link"]
                    command["game"] = GameOptions.CS
                    print("game")
                    command["currency"] = Currency.USD
                    print("currency")
                    response = steam_client_.steam_client.market.buy_item(**command)
                    print(response)
                    if response["wallet_info"]["success"] == 1:
                        count_success += 1
                        balance = steam_client_.initialize_account_balance()
                        await write_to_csv({"hash_name": item_name, "price": price + fee,
                                            "data_time": str(datetime.datetime.utcnow()), "float": float_value,
                                            "pattern": pattern})
                        length_items = await get_strings_length()
                        await send_async_request({"buy_ok": str(count_success),
                                                  "items_count": str(length_items),
                                                  "balance": str(balance),
                                                  "buy_items": {"hash_name": str(item_name), "price": str(price + fee),
                                                                "data_time": str(datetime.datetime.utcnow()),
                                                                "float": str(float_value), "pattern": str(pattern)}})
                        logger.info(f"Purchase successful: {response}")
                    else:
                        count_trying_buy_item += 1
                        await send_async_request({"buy_error": count_trying_buy_item})
                        print(f"Trying to buy count: {count_trying_buy_item}")
                        logger.warning(f"There was a problem buying this item. Trying to buy count: {count_trying_buy_item}")
                else:
                    logger.warning(f"Not enough balance {balance}")
    except asyncio.CancelledError:
        writer.close()
        await writer.wait_closed()
        logger.info("Client handler task cancelled.")
        raise
    except ApiException as e:
        count_trying_buy_item += 1
        await send_async_request({"buy_error": count_trying_buy_item})
        print(f"Trying to buy count: {count_trying_buy_item}")
        await logger.warning(f"There was a problem buying this item. Message: {e}")
    except Exception as e:
        count_trying_buy_item += 1
        await send_async_request({"buy_error": count_trying_buy_item})
        print(f"Trying to buy count: {count_trying_buy_item}")
        logger.warning(f"An unexpected error occurred: {e}")
    finally:
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()


async def run_server(steam_client):
    len_items = await get_strings_length()
    print(f"Amount of Purchased items: {len_items}")

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, steam_client, server),
        'localhost', 12351)

    async with server:
        try:
            logger.info("Server is running")
            print("Server is running")

            signal_handler_partial = functools.partial(signal_handler, server_task=server.serve_forever())
            signal.signal(signal.SIGINT, signal_handler_partial)

            await send_async_request({"items_count": len_items})
            await server.serve_forever()

        except asyncio.CancelledError:
            # This block can be triggered when 'stop' action is received
            server.close()
            await server.wait_closed()
            logger.warning("Server closed")
