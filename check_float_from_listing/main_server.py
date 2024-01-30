from dotenv import load_dotenv
import asyncio
import os
import aiohttp
import json
from listing.create_sessions import create_initial_proxy_session_connection, get_available_session, close_sessions
from listing.get_listing_float import fetch_data
from listing.globals import Shutdown_requested, save_data_on_exit, set_shutdown_flag
from listing.utils import logger, filter_dates_in_file, send_async_request
from proxies.proxies_list import proxies

count = 0
count_lock = asyncio.Lock()  # Lock for thread-safe counter increment
Sessions_ = None
command_queue = asyncio.Queue()
server = None


async def handle_client(reader, writer):
    global count, server
    try:
        while not Shutdown_requested:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode()
            command = json.loads(message)

            if command.get("action") == "stop":
                logger.exception("Received command Stop")
                server.close()
                set_shutdown_flag()
                await close_sessions(Sessions_)

                await server.wait_closed()
                logger.info("Server closed")
                save_data_on_exit(logger)
                break
            elif command.get("action") == "action":
                async with count_lock:
                    count += 1
                logger.info(f'Received command to fetch listing data. Count: {count} !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                enqueue_command(command)

    except asyncio.CancelledError:
        writer.close()
        await writer.wait_closed()
        logger.info("Client handler task cancelled.")
        raise

    finally:
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()


async def run_server():
    global server
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w),
        'localhost', 12350)

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            server.close()
            await server.wait_closed()
        if Shutdown_requested:
            server.close()
            await server.wait_closed()


def enqueue_command(command):
    asyncio.create_task(command_queue.put(command))


async def worker():
    while not Shutdown_requested:
        command = await command_queue.get()
        current_session = await get_available_session(Sessions_)

        if current_session:
            try:
                # Call process_command without asyncio.wait_for
                await process_command(command, current_session)

            except Exception as e:
                logger.exception(f"Error processing command: {e}")
            finally:
                command_queue.task_done()


async def process_command(command, session):
    try:
        url = command.get("url")
        conditions = command.get("conditions")
        sets_of_values = conditions.split(" | ")
        conditions_ = tuple(tuple(float(value) for value in set_.split(", ")) for set_ in sets_of_values)
        await fetch_data(session, url, conditions_, Sessions_)
    except aiohttp.ClientResponseError as e:
        # Handle the exception for non-2xx responses
        status_code = e.status
        reason = e.message
        print(f"API Error: {status_code} - {reason}")
        logger.exception(f"API exception during command processing: {status_code} - {reason}")
    except Exception as e:
        logger.exception(f"Error during command processing: {e}")


async def main():
    global Sessions_
    file_logs_path = os.getenv("PATH_TO_LOG_FILE_LISTING")
    filter_dates_in_file(file_logs_path)
    sessions = await create_initial_proxy_session_connection()
    logger.info(f"Amount of sessions created {len(sessions)}")
    not_working_proxies = len(proxies) - len(sessions)
    await send_async_request({"proxy_nowork_count": not_working_proxies})
    Sessions_ = sessions

    server_task = asyncio.create_task(run_server())
    workers = [asyncio.create_task(worker()) for _ in range(1000)]  # Example: 5 workers

    try:
        while not Shutdown_requested:
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        logger.exception("KeyboardInterrupt received, shutting down...")
        if not Shutdown_requested:
            set_shutdown_flag()
            if Sessions_:
                await close_sessions(Sessions_)

            save_data_on_exit(logger)
        logger.exception("Shutdown")

    for w in workers:  # Graceful shutdown of workers
        w.cancel()
    await asyncio.gather(server_task, *workers, return_exceptions=True)

    await close_sessions(sessions)
    logger.info("All sessions closed!")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
