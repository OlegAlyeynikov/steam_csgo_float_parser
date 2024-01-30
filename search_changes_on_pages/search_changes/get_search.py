import atexit
import signal
import asyncio
import aiohttp
from conditions.conditions_50 import conditions
from datetime import datetime
import time
import random
from urllib.parse import unquote
from search_changes.send_request_to_listing_module import main_send_command
from search_changes.utils import (get_header, load_user_agents_once, get_search_dict, logger,
                                  create_file_proxies_for_listing, read_proxies_from_file_txt, send_async_request)
from conditions.links import urls

MAX_CONCURRENT_REQUESTS = 110  # Define a semaphore to limit the number of concurrent requests
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
count_status_200 = count_status_429 = count_status_200_yes = count_status_200_no = 0
should_save_data = False  # Shared variable to indicate if data should be saved
should_continue = True
start_process_time = time.time()
Proxies_list = read_proxies_from_file_txt()
Search = get_search_dict()


async def fetch_data_price(session, proxy_, cookies, search_link):
    global count_status_200, count_status_429, count_status_200_yes, count_status_200_no
    header = get_header(cookie=cookies)
    try:
        async with semaphore:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(search_link, proxy=proxy_, ssl=False, headers=header, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        listing_search = data["results"]
                        for listing in listing_search:
                            for condition in conditions:
                                link_initial = condition[0]
                                item_part = link_initial.rsplit('/', 1)[-1]
                                hash_name = unquote(item_part)
                                if listing["name"] == hash_name or listing["hash_name"] == hash_name:
                                    # if hash_name in Search and Search[hash_name]["sell_listings"
                                    # ] != listing["sell_listings"] and listing["sell_listings"] != 0:
                                    if hash_name in Search and Search[hash_name]["sell_listings"] > listing[
                                        "sell_listings"] and listing["sell_listings"] != 0:
                                        Search[hash_name]["sell_listings"] = listing["sell_listings"]
                                        data_value = {
                                            "action": "action",
                                            "url": condition[0],
                                            "conditions": condition[1]
                                        }
                                        await main_send_command(data_value)
                                        count_status_200_yes += 1
                                        logger.info(
                                            f"Yes {count_status_200_yes} Time: {time.time() - start_process_time} Count {count_status_200}"
                                            f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                    else:
                                        Search[hash_name]["sell_listings"] = listing["sell_listings"]
                                        count_status_200_no += 1

                        count_status_200 += 1
                        logger.info(f"Success data Time: {time.time() - start_process_time} Count {count_status_200}")
                        return
                    else:
                        logger.warning(f"Empty price data, module: get_price.py")
                        return
                else:
                    if response.status == 429:
                        count_status_429 += 1
                        logger.warning(
                            f"Rate limited price. Count 429: {count_status_429} Time: {datetime.utcnow()}, module: get_price.py")
                        return
                    else:
                        logger.error(
                            f"Status code price: {response.status}, Failed to fetch data from module: get_price.py")
                        return

    except aiohttp.ClientError as e:
        logger.exception(f"Request exception module: get_price.py : {e}")
        return
    except (OSError, Exception) as e:
        logger.exception(f"Request timed out. {e}")
        return
    except aiohttp.ClientHttpProxyError as e:
        logger.exception(e)
        return


def get_proxy_from_proxies_list():
    if Proxies_list:
        proxy = Proxies_list.pop(0)
        Proxies_list.append(proxy)
        return proxy
    else:
        raise RuntimeError("No proxies available")


async def repeating_task(link_, session_index):
    attempts = 3
    for attempt in range(1, attempts + 1):
        if not should_continue:
            break
        try:
            proxy_new = get_proxy_from_proxies_list()
            initial_link = "https://steamcommunity.com/"
            header_start = get_header()
            cookies_ = None  # Initialize cookies_ to a default value

            async with aiohttp.ClientSession() as initial_session:
                async with initial_session.get(initial_link, proxy=proxy_new, ssl=False,
                                               headers=header_start) as initial_response:
                    if initial_response.status == 200:
                        cookie_header = initial_response.cookies
                        cookies_ = "; ".join([f"{key}={value.value}" for key, value in cookie_header.items()])
                        logger.info(f"Successfully initial request, module: get_price.py")
                    else:  # Handle the case where the initial request fails
                        logger.warning(
                            f"Attempt {attempt}: Initial request failed with status: {initial_response.status}")
                        if attempt < attempts:
                            # If it's not the last attempt, continue to the next iteration
                            continue
                        else:
                            raise Exception("All attempts to perform initial request failed")

                next_cookie_update = asyncio.get_event_loop().time() + random.randint(1 * 3600, 2 * 3600)

                while should_continue:
                    current_time = asyncio.get_event_loop().time()
                    await fetch_data_price(initial_session, proxy_new, cookies_, link_)
                    current_time_end = asyncio.get_event_loop().time()
                    elapsed_ = current_time_end - current_time
                    if current_time >= next_cookie_update:  # Update cookies
                        headers_refresh_cookie = get_header(url=link_, cookie=cookies_)
                        async with initial_session.get(link_, proxy=proxy_new, ssl=False,
                                                       headers=headers_refresh_cookie) as response:
                            if response.status == 200:
                                cookies_ = response.cookies
                            else:
                                logger.warning(
                                    f"Attempt {attempt}: Cookie update request failed with status: {response.status}")
                                if attempt < attempts:
                                    # If it's not the last attempt, continue to the next iteration
                                    continue
                                else:
                                    raise Exception("All attempts to update cookies failed")
                        next_cookie_update = current_time + random.randint(1 * 3600, 2 * 3600)
                    await asyncio.sleep(30 - elapsed_)

        except Exception as e:
            logger.error(f"Error in repeating_task: {e}")
        except aiohttp.ClientHttpProxyError as e:
            logger.error(e)
        except (OSError, Exception) as e:
            logger.error(f"Request timed out. {e}")
        finally:
            # Close the existing session to release resources
            if 'initial_session' in locals():
                await initial_session.close()


# async def repeating_task(proxy_new, link_, session_index):
#     initial_link = "https://steamcommunity.com/"
#     header_start = get_header()
#     cookies_ = None  # Initialize cookies_ to a default value
#     try:
#         async with aiohttp.ClientSession() as initial_session:
#             async with initial_session.get(initial_link, proxy=proxy_new, ssl=False,
#                                            headers=header_start) as initial_response:
#                 if initial_response.status == 200:
#                     cookie_header = initial_response.cookies
#                     cookies_ = "; ".join([f"{key}={value.value}" for key, value in cookie_header.items()])
#                     logger.info(f"Successfully initial request, module: get_price.py")
#                 else:  # Handle the case where the initial request fails
#                     logger.warning(f"Initial request failed with status: {initial_response.status}")
#             next_cookie_update = asyncio.get_event_loop().time() + random.randint(1 * 3600, 2 * 3600)
#
#             while should_continue:
#                 current_time = asyncio.get_event_loop().time()
#                 await fetch_data_price(initial_session, proxy_new, cookies_, link_)
#                 current_time_end = asyncio.get_event_loop().time()
#                 elapsed_ = current_time_end - current_time
#                 if current_time >= next_cookie_update:  # Update cookies
#                     headers_refresh_cookie = get_header(url=link_, cookie=cookies_)
#                     async with initial_session.get(link_, proxy=proxy_new, ssl=False,
#                                                    headers=headers_refresh_cookie) as response:
#                         if response.status == 200:
#                             cookies_ = response.cookies
#                     next_cookie_update = current_time + random.randint(1 * 3600,
#                                                                        2 * 3600)  # Set the next cookie update time
#                 await asyncio.sleep(60 - elapsed_)
#     except Exception as e:
#         logger.error(f"Error in repeating_task: {e}")
#     except aiohttp.ClientHttpProxyError as e:
#         logger.error(e)
#     except (OSError, Exception) as e:
#         logger.error(f"Request timed out. {e}")
#     finally:
#         # Close the existing session to release resources
#         if 'initial_session' in locals():
#             await initial_session.close()

async def handle_client(reader, writer):
    pass


async def run_server():
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w),
        'localhost', 12352)

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            server.close()
            await server.wait_closed()
        if not should_continue:
            server.close()
            await server.wait_closed()


async def schedule_tasks():
    global should_save_data, should_continue, Proxies_list
    len_urls = len(urls)
    print(len_urls)
    delay = 0.5 / len_urls  # Set the initial delay. 1/len_urls is each url checks each 1 second
    urls_new_list = urls * 60  # Multiply urls for tasks
    await send_async_request({"amount_proxies": len(Proxies_list)})
    len_proxies = len(urls_new_list)
    proxies_listing_list = Proxies_list[len_proxies:]
    Proxies_list = Proxies_list[:len_proxies]
    create_file_proxies_for_listing(proxies_listing_list)

    # Create a task to run the server concurrently
    server_task = asyncio.create_task(run_server())

    tasks = []
    start_time_ = asyncio.get_event_loop().time()
    for i, url_ in enumerate(urls_new_list):
        # proxy = get_proxy_from_proxies_list()
        task = asyncio.create_task(repeating_task(url_, i))
        tasks.append(task)
        start_time_ += delay  # Increase the start time for the next session
        await asyncio.sleep(delay)

    print(f"Sessions created: {len(tasks)}")

    await asyncio.gather(*tasks)

    # Keep the script running
    while should_continue:
        await asyncio.sleep(5)

    should_save_data = True

    # Wait for the server task to complete
    await server_task


# async def schedule_tasks():
#     global should_save_data, should_continue
#     len_urls = len(urls)
#     print(len_urls)
#     delay = 0.5 / len_urls  # Set the initial delay. 1/len_urls is each url checks each 1 second
#     urls_new_list = urls * 120  # Multiply urls for tasks
#     len_proxies = len(urls_new_list)
#     proxies_listing_list = Proxies_list[len_proxies + 1:]
#     create_file_proxies_for_listing(proxies_listing_list)
#     tasks = []
#     start_time_ = asyncio.get_event_loop().time()
#     for i, url_ in enumerate(urls_new_list):
#         proxy = get_proxy_from_proxies_list()
#         task = asyncio.create_task(repeating_task(proxy, url_, i))
#         tasks.append(task)
#         start_time_ += delay  # Increase the start time for the next session
#         await asyncio.sleep(delay)
#     print(f"Len tasks : {len(tasks)}")
#     await send_async_request({"len_search_sessions": len(tasks)})
#
#     await asyncio.gather(*tasks)
#
#     # Keep the script running
#     while should_continue:
#         await asyncio.sleep(5)
#
#     should_save_data = True


def save_data_on_exit():  # Define your signal handler to save data on exit
    if should_save_data:
        print(f"Current time: {datetime.utcnow()}")
        print(f"Elapsed time: {time.time() - start_process_time:.2f} seconds")
        print(f"Success count: {count_status_200}")
        print(f"Rate limited count: {count_status_429}")
        print(f"Commands sent: {count_status_200_yes}")
        print(f"Count No: {count_status_200_no}")


atexit.register(save_data_on_exit)  # Register the atexit function to save data on exit


def interrupt_handler(loop):  # Pass the event loop
    global should_save_data, should_continue
    logger.info("Interrupt signal received. Stopping the loops and saving data.")
    should_continue = False
    should_save_data = True
    save_data_on_exit()


async def main_():
    # global_logger = await setup_async_logging()
    # await initialize_logger()
    # await asyncio.sleep(1)
    try:
        # await send_async_request({"items_count": len(conditions)})  # Assuming conditions is defined somewhere
        load_user_agents_once()
        loop = asyncio.get_running_loop()
        signal.signal(signal.SIGINT, lambda signum, frame: interrupt_handler(loop))  # Use lambda to pass the loop
        await schedule_tasks()
    except Exception as e:
        logger.exception(f"An error occurred in main_: {e}")

# # Usage in your main function
# async def main_():
#     await send_async_request({"items_count": len(conditions)})
#     load_user_agents_once()
#     loop = asyncio.get_running_loop()
#     signal.signal(signal.SIGINT, lambda signum, frame: interrupt_handler(loop))  # Use lambda to pass the loop
#     await schedule_tasks()


#  ssh root@49.13.26.115
# pass: HhEEPxLUT4WXegEVFdxx1
# screen -d -r csgo
# Ctrl + C
# node index.js

# ssh csfloat@78.47.98.155
# l: csfloat
# p: Ndj32js39

# screen -d -r steem_items is trying to reattach a detached screen session named steem_items.
# List Existing Screen Sessions: Use the command screen -ls
# create new screen session:  screen -S steem_items
# eturn you to your original terminal session:  Ctrl+A followed by D.
# You can then reattach using screen -d -r steem_items.
# Check for Existing Processes: 'ps aux | grep [process name]'

# ssh csfloat@142.132.148.184
# pass: CSgo1008

# reboot server session connection
# sudo shutdown -r now

#  screen -S steam_items

# screen -d -r steam_items
# screen -d -r steam_items1
# screen -d -r steam_items2

# sudo lsof -i -P -n | grep LISTEN   all ports which running
# sudo kill -9 PID    kill port    PID is identificator of port

# copy from server to pc
# scp -r -P PORT_NUMBER username@server:/path/to/source /path/to/destination
# scp -r -P 31122 csfloat@5.9.36.102:/home/csfloat/web2 /Users/stoveprofi
