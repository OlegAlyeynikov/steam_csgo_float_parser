import os
import time
from datetime import datetime
import aiohttp

import re
import random
import string

from listing.create_sessions import initialize_session_for_proxy
from listing.globals import (Items, floats_count, rate_limited_listing_count, success_listing_count,
                             start_time_, time_out_count)
from listing.save_data_in_file import save_data_to_csv, save_response_time_csv
from listing.utils import logger, send_command_and_buy_item, send_async_request

start_time_()


# Function to generate a random SID
async def generate_random_sid():
    sid_length = 9
    sid_chars = string.digits
    return ''.join(random.choice(sid_chars) for _ in range(sid_length))


async def change_sid_to_random(proxy):
    # Extract current SID from the proxy string
    match = re.search(r'sid-(\d+)-1', proxy)
    if match:
        current_sid = match.group(1)
        # Generate a random SID
        new_sid = generate_random_sid()
        # Replace the current SID with the new SID in the proxy string
        new_proxy = proxy.replace(f"sid-{current_sid}-1", f"sid-{new_sid}")
        return new_proxy
    else:
        # If the current SID is not found in the proxy string, return the original proxy
        return proxy


async def fetch_data(session_info, link, conditions,  sessions_):
    start_time = time.time()
    start_time_datetime = datetime.utcnow()
    try:
        for condition_ in conditions:
            float_min = condition_[0]
            float_max = condition_[1]
            pattern = condition_[2]
            min_price = condition_[3]
            max_price = condition_[4]
            listing_link = link + os.getenv("URL_RENDER_LISTING")
            float_conditions = (float_min, float_max, pattern,)
            headers_ = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-GB;q=1.0, en;q=0.5",
                "Connection": "keep-alive",
                "Host": "steamcommunity.com",
                # "If-Modified-Since": if_modified,
                "Cache-Control": "no-cache",
                "Referer": listing_link,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.6; rv:41.0) Gecko",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": session_info.cookies
            }
            timeout = aiohttp.ClientTimeout(total=10)
            async with session_info.session.get(
                    listing_link, proxy=session_info.proxy, ssl=False, headers=headers_, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        listing = dict(data['listinginfo'])
                        for id_, value in listing.items():
                            if id_ not in Items:
                                if "converted_price" and "converted_fee" in listing[id_]:
                                    fee = listing[id_]["converted_fee"]
                                    price = listing[id_]["converted_price"] + fee
                                    min_price = min_price
                                    max_price = max_price
                                    if min_price <= price <= max_price:
                                        asset_link = value['asset']['market_actions'][0]["link"]
                                        listing_id = id_
                                        asset_id = value['asset']['id']
                                        base_url = os.getenv("URL_TO_FLOAT_MODULE_JS") + asset_link
                                        # Define the placeholders
                                        listing_id_placeholder = "%listingid%"
                                        asset_id_placeholder = "%assetid%"
                                        # Replace the placeholders with the provided values
                                        modified_url = base_url.replace(listing_id_placeholder, str(listing_id))
                                        url_ = modified_url.replace(asset_id_placeholder, str(asset_id))
                                        # http://49.13.26.115:8080/?url=steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M4651722584180855533A35372418756D12447963313779051657
                                        Items[listing_id] = {'price': price,
                                                             'asset_id': asset_id,
                                                             'listing_id': listing_id,
                                                             }
                                        await fetch_data_in_floats_list(url_, session_info, listing_id,
                                                                        float_conditions, link, fee, price)
                                        await save_data_to_csv(
                                            {listing_id: Items[listing_id]},
                                            os.getenv("PATH_TO_LISTING_ITEMS_CSV_DB"))
                                    else:
                                        continue
                                else:
                                    logger.warning("No converted_price")
                                    continue
                            else:
                                continue
                        await save_response_time_csv(response.status, session_info.proxy, start_time_datetime)
                        success = success_listing_count()
                        await send_async_request({"proxy_work_count": success})
                        all_data_time = time.time()
                        logger.info(f"Success listing. Get all data {all_data_time - start_time} "
                                    f"Count 200: {success}")
                        return
                    else:
                        await save_response_time_csv(response.status, session_info.proxy, start_time_datetime)
                        logger.warning(f"Empty data listing")
                        return
                else:
                    if response.status == 429:
                        rate_lim_count = rate_limited_listing_count()
                        await send_async_request({"proxy_bad": rate_lim_count})
                        await save_response_time_csv(response.status, session_info.proxy, start_time_datetime)
                        logger.warning(f"Rate limited listing. Count 429: {rate_lim_count}")

                        if "sid" in session_info.proxy:
                            new_proxy = await change_sid_to_random(session_info.proxy)
                            await session_info.close()
                            # Create a new session with a new SID
                            new_session_info = await initialize_session_for_proxy(new_proxy)
                            sessions_.append(new_session_info)
                            logger.info(f"New session created with a new SID")

                        return
                    else:
                        await save_response_time_csv(response.status, session_info.proxy, start_time_datetime)
                        logger.error(f"Status code listing: {response.status}, "
                                     f"Failed to fetch data from {link}")
                        return
    except aiohttp.ClientError as e:
        logger.exception(f"Request exception proxy: {session_info.proxy}: {e}")
        return
    except aiohttp.client_exceptions.ServerDisconnectedError:
        logger.error("Server disconnected. Closing and removing the session.")
        await session_info.close()
        if session_info in sessions_:
            sessions_.remove(session_info)
        return
    except (OSError, Exception) as e:
        timeout_count = time_out_count()
        await send_async_request({"proxy_slow": timeout_count})
        logger.warning(f"Request timed out. {e} Count: {timeout_count}")
        return
    except aiohttp.ClientHttpProxyError as e:
        logger.error(e)
        return
    finally:
        # Close the existing session to release resources
        if 'initial_session' in locals():
            await session_info.session.close()
        return


async def fetch_data_in_floats_list(url: str, session, listing_id_, conditions_, initial_link, fee_, price_):
    float_min = conditions_[0]
    float_max = conditions_[1]
    pattern_ = conditions_[2]
    try:
        async with session.session.get(url) as resp:
            if resp.status == 200:
                data_ = await resp.json()
                if data_:
                    float_value = data_['iteminfo']['floatvalue']
                    pattern_value = data_['iteminfo']['paintseed']
                    Items[listing_id_]['float_value'] = float_value
                    Items[listing_id_]['pattern_value'] = pattern_value
                    Items[listing_id_]['initial_link'] = initial_link
                    if float_min <= float_value <= float_max:
                        logger.info(f"Success float data: {float_value}, time: {datetime.utcnow()}, "
                                    f"link: {initial_link} float: {float_value}")
                        await send_command_and_buy_item(
                            initial_link, listing_id_, price_, fee_, float_value, pattern_value)
                    elif pattern_value == pattern_:
                        logger.info(f"Success pattern data: {pattern_value},  time: {datetime.utcnow()}, "
                                    f"link: {initial_link} pattern: {pattern_value}")
                        await send_command_and_buy_item(
                            initial_link, listing_id_, price_, fee_, float_value, pattern_value)
                    else:
                        logger.info(f"Success float: {float_value} Count: {floats_count()}")

                else:
                    logger.warning(f"Empty float, pattern data")
            else:
                if resp.status == 429:
                    logger.warning(f"Rate limited for float, pattern data")
                else:
                    logger.error(
                        f"Status code: {resp.status}, Failed fetch float, url: {url}")
    except aiohttp.ClientError as e:
        logger.exception(f"ConnectionError float: {e}")
