import csv
import datetime
import os
import aiofiles


def read_data_from_csv(csv_file):
    data = {}
    try:
        with open(csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print(reader)
            for row in reader:
                data[row['listing_id']] = row
        return data
    except Exception as e:
        print(f"Error reading data from {csv_file}: {e}")
        return {}


async def save_data_to_csv(data, file_name):
    items = [item for key, item in data.items()]
    if not items:
        print("No data to write.")
        return
    fieldnames = items[0].keys()
    # Check if the file already exists to avoid writing headers again
    try:
        async with aiofiles.open(file_name, 'r') as csvfile:
            existing = await csvfile.read(1)
    except FileNotFoundError:
        existing = ''

    async with aiofiles.open(file_name, 'a', newline='') as csvfile:  # Open in append mode
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not existing:  # If file didn't exist or was empty, write the header
            await writer.writeheader()
        for row in items:
            await writer.writerow(row)


async def save_response_time_csv(resp_status, proxy_1, try_proxy_time):
    response_time = {
        proxy_1: {
            'resp_status': resp_status,
            'proxy_get_page_with_items': proxy_1,
            'start_time': try_proxy_time,
            'elapsed_time': str(datetime.datetime.utcnow() - try_proxy_time),
        }
    }
    await save_data_to_csv(response_time, os.getenv("PATH_TO_TIME_LOG_CSV"))
