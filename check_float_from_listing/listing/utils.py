import logging
import os
import random
import time
from datetime import datetime, timedelta
from email.utils import formatdate
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse, unquote
import aiohttp
import pandas as pd
from dotenv import load_dotenv
from listing.globals import change_user_agent_list, User_agent_list
from listing.send_request_to_buy_module import main_send_command

Enable_console_log = True
load_dotenv()


def cleanup_old_logs(log_file, days_to_keep):
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        for handler in logging.getLogger('my_logger').handlers:
            if isinstance(handler, RotatingFileHandler):
                for filename in [handler.baseFilename, handler.baseFilename + ".1", handler.baseFilename + ".2"]:
                    try:
                        file_date = datetime.fromtimestamp(os.path.getctime(filename))
                        if file_date < cutoff_date:
                            os.remove(filename)
                            print(f"Removed old log file: {filename}")
                    except FileNotFoundError:
                        pass
    except Exception as e:
        print(f"Error during log cleanup: {e}")


def setup_logging(enable_console=True):
    logger_ = logging.getLogger('my_logger')
    logger_.setLevel(logging.DEBUG)

    # Set up a rotating file handler with max log size and backup count
    log_file = os.getenv("PATH_TO_LOG_FILE_LISTING")
    max_log_size_bytes = 1e6  # 1 MB
    backup_count = 3

    fh = RotatingFileHandler(log_file, maxBytes=int(max_log_size_bytes), backupCount=backup_count)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger_.addHandler(fh)

    # Set up the console handler if enabled
    if enable_console:
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)
        logger_.addHandler(sh)

    # Perform log cleanup: remove log files older than three days
    cleanup_old_logs(log_file, days_to_keep=1)

    return logger_


logger = setup_logging(enable_console=Enable_console_log)  # Set enable_console to False to disable console logs


async def send_async_request(data):
    url = 'http://127.0.0.1:8088/update_data/'
    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
        except aiohttp.ClientResponseError as cre:
            print(f"ClientResponseError: {cre}")
        except aiohttp.ClientConnectionError as cce:
            print(f"ClientConnectionError: {cce}")


async def get_market_order_headers(referer="https://steamcommunity.com", cookie=None):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB;q=1.0, en;q=0.5",
        "Connection": "keep-alive",
        "Host": "steamcommunity.com",
        # "If-Modified-Since": if_modified,
        # "Cookie": cookie,
        "Cache-Control": "no-cache",
        "Referer": referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.6; rv:41.0) Gecko",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        headers["Cookie"] = cookie
        return headers
    elif User_agent_list:
        agent = change_user_agent_list()
        headers["User-Agent"] = agent
        start_year = 2022
        today = datetime.now()
        start_date = datetime(start_year, 1, 1)
        delta = (today - start_date).days
        random_days = random.randint(0, delta)
        random_past_date = start_date + timedelta(days=random_days)
        past_time = random_past_date.timestamp()
        headers["If-Modified-Since"] = formatdate(timeval=past_time, localtime=False,
                                                  usegmt=True)  # Format this time as an RFC 2822-compliant date string
        return headers
    else:
        raise RuntimeError("No user agent available")


def proxy_rotation(proxy_dict):
    now = time.time()
    closest_time = min(proxy_dict.keys(), key=lambda k: abs(k - now))  # Find the key that is closest to the current t
    future_times = [k for k in proxy_dict.keys() if k >= now]
    if future_times:
        selected_time = min(future_times)  # If there are future times, use the one that is closest to 'now'
    else:
        selected_time = closest_time
    return proxy_dict[selected_time]


async def send_command_and_buy_item(initial_link, listing_id_, price_, fee_, float_, pattern):
    market_name = unquote(urlparse(str(initial_link)).path.split('/')[-1])
    buy_command = {
        "initial_link": initial_link,
        'action': 'action',
        'market_name': market_name,
        'market_id': listing_id_,
        'price': price_,
        'fee': fee_,
        'float': float_,
        'pattern': pattern

        # 'game': GameOptions.CS,  # This should be a string like 'CSGO'
        # 'currency': Currency.USD  # This should be a string like 'USD'
    }

    await main_send_command(buy_command)


def filter_dates_in_file(file_path):
    try:
        df = pd.read_csv(file_path)
        date_column = 'start_time'  # Replace with the actual column name containing dates
        df[date_column] = pd.to_datetime(df[date_column])

        # Filter dates less than seven days old
        seven_days_ago = datetime.now() - timedelta(days=3)
        filtered_df = df[df[date_column] >= seven_days_ago]

        # Save the filtered dataframe back to the file
        filtered_df.to_csv(file_path, index=False)

        print(f"Filtered logs in {file_path} and saved successfully.")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
