import os
import aiohttp
import logging
from datetime import datetime, timedelta
from email.utils import formatdate
import random
from logging.handlers import RotatingFileHandler
from conditions.conditions_50 import conditions
from urllib.parse import unquote
from dotenv import load_dotenv

user_agents = []
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
    log_file = os.getenv("PATH_TO_SEARCH_LOG_FILE")
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


def get_random_past_date_header(start_year=2022) -> str:
    """
    Function that generates a random If-Modified-Since header
    value with a date ranging from 2022 to today
    :param start_year:
    :return: str
    """
    today = datetime.now()
    start_date = datetime(start_year, 1, 1)
    delta = (today - start_date).days
    random_days = random.randint(0, delta)
    random_past_date = start_date + timedelta(days=random_days)
    past_time = random_past_date.timestamp()
    return formatdate(timeval=past_time, localtime=False, usegmt=True)


def get_market_order_headers(agent, language, referer="https://steamcommunity.com", cookie=None):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": language,
        "Connection": "keep-alive",
        "Host": "steamcommunity.com",
        # "If-Modified-Since": if_modified,
        # "Cookie": cookie,
        "Cache-Control": "no-cache",
        "Referer": referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": agent,
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        headers["Cookie"] = cookie
        return headers
    else:
        headers["If-Modified-Since"] = get_random_past_date_header()
        return headers


def load_user_agents():
    user_agent_path = os.getenv("PATH_TO_USER_AGENT")
    with open(user_agent_path, "r", encoding="UTF-8",
              errors="ignore") as file:
        lines = file.readlines()
    cleaned_user_agents = map(lambda agent: agent.strip(), lines)
    user_agent_ = list(cleaned_user_agents)
    return user_agent_


def load_user_agents_once():
    # Load user agents from file and store them in the global list
    global user_agents
    user_agents = load_user_agents()  # Assuming load_user_agents reads the file and returns a list of agents


def get_user_agent():
    if user_agents:
        agent = user_agents.pop(0)
        user_agents.append(agent)
        return agent
    else:
        raise RuntimeError("No user agent available")


def get_header(url=None, cookie=None):
    language = "en-GB;q=1.0, en;q=0.5"
    user_agent = get_user_agent()
    header = get_market_order_headers(
        user_agent, language, url if url is not None else '', cookie if cookie is not None else '')
    return header


def get_search_dict() -> dict:
    search = {}
    for condition in conditions:
        link_initial = condition[0]
        item_part = link_initial.rsplit('/', 1)[-1]
        hash_name = unquote(item_part)
        if hash_name not in search:
            search[hash_name] = {"sell_listings": 0}
    return search


def read_proxies_from_file_txt() -> list:
    proxy_path = os.getenv("PATH_TO_PROXY_LIST")
    proxy_list = []
    try:
        with open(proxy_path, 'r') as file:
            for line in file:
                parts = line.strip().split(':')
                if len(parts) == 4:
                    ip, port, username, password = parts
                    proxy_url = f'http://{username}:{password}@{ip}:{port}'
                    proxy_list.append(proxy_url)
                elif len(parts) == 2:
                    ip, port = parts
                    proxy_url = f'http://{ip}:{port}'
                    proxy_list.append(proxy_url)
        return proxy_list
    except FileNotFoundError:
        print(f"File '{proxy_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def create_file_proxies_for_listing(proxy_list: list):
    path_to_file = os.getenv("PATH_TO_LISTING_PROXIES")
    with open(path_to_file, 'w') as python_file:
        python_file.write("proxies = [\n")
        for proxy in proxy_list:
            python_file.write(f'    "{proxy}",\n')
        python_file.write("]\n")


async def send_async_request(data):
    # url = 'http://192.168.33.11:8088/update_data/'
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
