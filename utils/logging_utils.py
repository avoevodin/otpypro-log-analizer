"""
Module for logging
"""
import getpass
import logging
import os
import socket


def get_extra_data() -> dict:
    """
    Some extra data for logging.
    :return: dict with extra data
    """
    return {
        "clientip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def logging_info(message: str) -> None:
    """
    Execute logging.info with passed message and some extra data.
    :param message:
    :return:
    """
    logging.info(message, extra=get_extra_data())


def logging_error(message: str) -> None:
    """
    Execute logging.error with passed message and some extra data.
    :param message:
    :return:
    """
    logging.error(message, extra=get_extra_data())


def logging_exception(message: str) -> None:
    """
    Execute logging.exception with passed message and some extra data.
    :param message:
    :return:
    """
    logging.exception(message, extra=get_extra_data(), exc_info=True)


def setup_logging(conf: dict) -> None:
    """
    Initial logging setup.
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
