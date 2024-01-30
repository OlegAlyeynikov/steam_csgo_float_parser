import csv
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import aiofiles
import aiohttp
import requests
from dotenv import load_dotenv

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


async def send_async_request(data):
    url = 'http://127.0.0.1:8088/update_data/'
    headers = {'Content-Type': 'application/json'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                status_code = response.status
                print(f"Request sent successfully status code: {status_code}")
    except requests.exceptions.RequestException as e:
        # Log the error
        logger.error(f"Failed to send request: {e}")
    except aiohttp.client_exceptions.ClientConnectorError as e:
        # Log the specific connection error
        logger.error(f"Connection error: {e}")
        # Handle the error or take corrective action if needed


def setup_logging():
    logger_ = logging.getLogger('my_logger')
    logger_.setLevel(logging.DEBUG)

    # Set up a rotating file handler with max log size and backup count
    log_file = os.getenv("PATH_TO_BUY_MODULE_LOG_FILE")
    max_log_size_bytes = 1e6  # 1 MB
    backup_count = 3

    fh = RotatingFileHandler(log_file, maxBytes=int(max_log_size_bytes), backupCount=backup_count)
    fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)

    logger_.addHandler(fh)
    logger_.addHandler(sh)

    # Perform log cleanup: remove log files older than three days
    cleanup_old_logs(log_file, days_to_keep=7)

    return logger_


logger = setup_logging()


async def write_to_csv(data, filename=os.getenv("PATH_TO_BUY_ITEMS_CSV_DB")):
    async with aiofiles.open(filename, mode='a') as file:
        csv_line = f'"{data["hash_name"]}","{data["price"]}","{data["data_time"]}","{data["float"]}","{data["pattern"]}"\n'
        await file.write(csv_line)


async def get_strings_length(filename=os.getenv("PATH_TO_BUY_ITEMS_CSV_DB")):
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Assuming the strings are in the first column of the CSV file
        strings_lengths = [len(row[0]) for row in reader]

    return len(strings_lengths)


def send_request_to_interface(data):
    url = 'http://127.0.0.1:8088/update_data/'
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        logger.info(f"Request sent successfully. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send request: {e}")
