import time
import os
from datetime import datetime
from listing.save_data_in_file import read_data_from_csv
from dotenv import load_dotenv

load_dotenv()
Items = read_data_from_csv(os.getenv("PATH_TO_LISTING_ITEMS_CSV_DB"))
Success_float_count = 0
Success_listing_count_ = 0
Rate_limited_listing = 0
Start_time = time.time()
Shutdown_requested = False
Time_out_count = 0


def load_user_agents():
    path_to_user_agents = os.getenv("PATH_TO_USER_AGENTS_TXT")
    with open(path_to_user_agents, "r", encoding="UTF-8", errors="ignore") as file:
        lines = file.readlines()
    cleaned_user_agents = map(lambda agent: agent.strip(), lines)
    return list(cleaned_user_agents)


User_agent_list = load_user_agents()


def change_user_agent_list():
    global User_agent_list
    agent = User_agent_list.pop(0)
    User_agent_list.append(agent)
    return agent


def time_out_count():
    global Time_out_count
    Time_out_count += 1
    return Time_out_count


def set_shutdown_flag():
    global Shutdown_requested
    Shutdown_requested = True
    

def start_time_():
    global Start_time
    Start_time = time.time()
    return Start_time


def success_listing_count():
    global Success_listing_count_
    Success_listing_count_ += 1
    return Success_listing_count_


def floats_count():
    global Success_float_count
    Success_float_count += 1
    return Success_float_count


def rate_limited_listing_count():
    global Rate_limited_listing
    Rate_limited_listing += 1
    return Rate_limited_listing


def save_data_on_exit(logger):  # Define your signal handler to save data on exit
    elapsed_time = time.time() - Start_time
    current_time_exit = datetime.utcnow()
    logger.info(f"Current time: {current_time_exit}")
    logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
    logger.info(f"Success count: {Success_listing_count_}")
    logger.info(f"Rate limited count: {Rate_limited_listing}")
    logger.info(f"Timeout count: {Time_out_count}")
