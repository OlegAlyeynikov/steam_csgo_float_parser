import asyncio
import time

import aiohttp

from listing.utils import get_market_order_headers, logger
from proxies.proxies_list import proxies

proxies_for_sessions = proxies.copy()


class SessionInfo:
    def __init__(self, session, proxy, cookies):
        self.session = session
        self.proxy = proxy
        self.cookies = cookies
        self.last_used = time.time()

    async def close(self):
        await self.session.close()


async def initialize_session_for_proxy(proxy: str, timeout=15):
    initial_link = "https://steamcommunity.com/"
    header_start = await get_market_order_headers()  # Define this function as per your needs

    session = aiohttp.ClientSession()
    try:
        async with session.get(initial_link, proxy=proxy, ssl=True, headers=header_start, timeout=timeout) as response:
            if response.status == 200:
                cookies_ = "; ".join([f"{key}={value.value}" for key, value in response.cookies.items()])
                logger.info(f"Successfully proxy for listing initial request")
                return SessionInfo(session, proxy, cookies_)
            else:
                logger.warning(f"Initial request for listing failed with status: {response.status}")
                await session.close()
                return None
    except Exception as e:
        logger.error(f"Exception during session initialization: {e}")
        await session.close()
    except aiohttp.ClientHttpProxyError as e:
        logger.error(e)
    except (OSError, Exception) as e:
        logger.error(f"Request timed out. {e}")
    finally:
        # Close the existing session to release resources
        if 'initial_session' in locals():
            await session.close()


async def get_available_session(sessions):
    if not sessions:
        return None  # Return None if there are no sessions

    # Use the min function with a custom key to find the least recently used session
    least_recently_used_session = min(sessions, key=lambda session_info: session_info.last_used)

    # Update the last_used time for the selected session
    least_recently_used_session.last_used = time.time()

    return least_recently_used_session


async def create_initial_proxy_session_connection():
    tasks = [initialize_session_for_proxy(proxy, timeout=15) for proxy in proxies_for_sessions]
    session_data = await asyncio.gather(*tasks)

    # Filter out None values if any session initialization failed
    sessions = [data for data in session_data if data is not None]
    return sessions


async def close_sessions(sessions):
    logger.info("Recieved signal to close all sessions!")
    # Close each session in the sessions list
    if sessions:
        await asyncio.gather(*(session.close() for session in sessions))
        logger.info("All sessions have been closed.")
    else:
        logger.info("No sessions to close.")
