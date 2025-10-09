from rich.console import Console
from rich_logger import
import logging
import datetime

    now = datetime.datetime.now()
    FORMATTED_NOW = now.strftime('%m-%d-%Y_%I:%M:%S_%p')
    LOG_BASE = "/Users/maxludden/dev/supergene/logs/"

    loggers = {}

    def myLogger(name):
    global loggers
    log_path = LOG_BASE + name + '/' + FORMATTED_NOW + '.log'

    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        loggers[name] = logger

    return logger
