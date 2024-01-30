import asyncio
import json
import os

import steampy.exceptions
from dotenv import load_dotenv
from steampy.client import SteamClient

from buy_module.utils import send_request_to_interface

load_dotenv()


def are_credentials_filled(config_file) -> bool:
    with open(config_file) as file:
        config = json.load(file)
        return all(config.values())


class SteamBot:
    def __init__(self, config_file, steam_guard_file):
        with open(config_file) as file:
            config = json.load(file)

        self.api_key = config['api_key']
        self.username = config['username']
        self.password = config['password']
        self.currency = config['currency']
        self.steam_guard = steam_guard_file

        self.cookies = self.get_cookies()
        # self.proxies = self.get_proxies()
        self.steam_client = SteamClient(
            api_key=self.api_key,
            username=self.username,
            password=self.password,
            steam_guard=self.steam_guard,
            login_cookies=self.cookies)
        # self.steam_client = SteamClient(
        #     api_key=self.api_key,
        #     username=self.username,
        #     password=self.password,
        #     steam_guard=self.steam_guard,
        #     login_cookies=self.cookies,
        #     proxies=self.proxies)

        self.balance = None
        # self.buy_order_limit = None
        # self.total_cost = None
        # self.ordered_items_dict = {}
        self.items_list = []
        self.command_queue = asyncio.Queue()

    @staticmethod
    def get_cookies():
        # if os.path.exists(os.getenv("PATH_TO_COOKIES")):
        #     with open(os.getenv("PATH_TO_COOKIES"), 'r', encoding='utf-8') as cookies_file:
        #         return json.load(cookies_file)
        # else:
        #   return None
        return None

    @staticmethod
    def get_proxies():
        if os.path.exists(os.getenv("PATH_TO_PROXY")):
            with open(os.getenv("PATH_TO_PROXY")) as proxies_file:
                return json.load(proxies_file)
        else:
            return None

    @staticmethod
    def login_required(func):
        def func_wrapper(self, *args, **kwargs):
            if self.steam_client.was_login_executed is not True:
                print("Login method was not used.  Attempting to log in...")
                self.login()
            return func(self, *args, **kwargs)

        return func_wrapper

    def login(self):
        try:
            self.steam_client.login()
            print(f"Successfully Logged in {self.username}")
        except steampy.exceptions.InvalidCredentials:
            print("Wrong credentials.")
            exit(1)
        except steampy.exceptions.CaptchaRequired:
            print("Captcha appeared, try again later.")
            exit(1)
        except Exception as ex:
            print(f"Failed to login into account: {str(ex)}")
            exit(1)
        return self.steam_client

    @login_required
    def initialize_account_balance(self):
        """
        Getting account balance and Buy Order limit.
        """
        try:
            # Initialize and print account balance
            self.balance = self.steam_client.get_wallet_balance()
            print(f"Balance: {self.balance} {self.currency}")

            return self.balance
        except Exception as ex:
            print(f"Failed to initialize account balance: {str(ex)}")
            exit(1)

    @login_required
    def save_cookies(self):
        try:
            with open(os.getenv("PATH_TO_COOKIES"), 'w',
                      encoding='utf-8') as cookies_file:
                json.dump(self.steam_client._session.cookies.get_dict(), cookies_file)
                print("Saved cookies")
        except Exception as ex:
            print(f"Couldn't save cookies: {ex}")

    def main(self):
        config_file = os.getenv("PATH_TO_CONFIG")
        if not are_credentials_filled(config_file):
            print('Please fill missing credentials in config.json')
            exit(1)
        self.save_cookies()

        balance = self.initialize_account_balance()
        send_request_to_interface({"balance": str(balance)})

    def cleanup(self):
        print("Performing cleanup...")
        # Logout from the Steam client
        try:
            self.steam_client.logout()
            print("Logged out from Steam client.")
        except Exception as e:
            print(f"Error during logout: {e}")
