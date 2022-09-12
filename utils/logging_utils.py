"""
Module for logging
"""
import getpass
import logging
import os
import socket
from logging import LoggerAdapter


def get_extra_data() -> dict:
    """
    Some extra data for logging.
    :return: dict with extra data
    """
    return {
        "clientip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def get_logger_adapter(name: str, conf: dict) -> LoggerAdapter:
    """
    Return logger adapter with init settings.
    :param name: module name
    :param conf: app configs
    :return:
    """
    log_dir = conf.get("LOG_DIR")
    log_filename = conf.get("LOGS_FILENAME")
    logs_path = None
    if log_dir and log_filename:
        logs_path = os.path.join(log_dir, log_filename)
    logging.basicConfig(
        filename=logs_path,
        format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level=conf.get("LOG_LEVEL") or "DEBUG",
    )
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, get_extra_data())
