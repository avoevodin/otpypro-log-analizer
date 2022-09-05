"""
TODO
"""
import logging
import socket
import getpass


def get_extra_data():
    """TODO"""
    return {
        "clientip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def logging_info(message):
    """TODO"""
    logging.info(message, extra=get_extra_data())
