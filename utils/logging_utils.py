"""
TODO
"""
import getpass
import logging
import socket


def get_extra_data() -> None:
    """TODO"""
    return {
        "clientip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def logging_info(message: str) -> None:
    """TODO"""
    logging.info(message, extra=get_extra_data())


def logging_error(message: str) -> None:
    """TODO"""
    logging.error(message, extra=get_extra_data())


def logging_warning(message: str) -> None:
    """TODO"""
    logging.warning(message, extra=get_extra_data())


def logging_exception(message: str) -> None:
    """TODO"""
    logging.exception(message, extra=get_extra_data(), exc_info=True)


def setup_logging(conf: dict) -> None:
    """TODO"""
    logging.basicConfig(
        filename=conf.get("LOGS_FILENAME"),
        format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level=conf.get("LOG_LEVEL") or "DEBUG",
    )
