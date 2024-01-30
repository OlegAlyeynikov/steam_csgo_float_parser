import subprocess
import time
import os
import logging


def configure_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger('django')


logger = configure_logging()


def start_process(script_path, port, venv_path, delay):
    python_interpreter = os.path.join(os.path.join(venv_path, 'bin', 'python3'))
    subprocess.Popen([python_interpreter, script_path, str(port)])
    logger.info('!!!!!!!!!!Started process "%s" with port %d and delay %d seconds.', script_path, port, delay)
    time.sleep(delay)


def start_child_processes(processes):
    for script_path, venv_path, port, delay in processes:
        start_process(script_path, port, venv_path, delay)
