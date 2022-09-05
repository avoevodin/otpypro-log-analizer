"""
TODO
"""
from datetime import datetime
import logging
import socket
import getpass
from pathlib import Path


def get_extra_data():
    """TODO"""
    return {
        "clientip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def logging_info(message):
    """TODO"""
    logging.info(message, extra=get_extra_data())


def logging_exception(message):
    """TODO"""
    logging.exception(message, extra=get_extra_data())


def setup_logging(conf: dict):
    """TODO"""
    logging.basicConfig(
        filename=conf.get("LOGS_FILENAME"),
        format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level="INFO",
    )
