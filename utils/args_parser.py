"""
Parse args passed to cli
"""

import argparse
from argparse import Namespace


def get_parsed_args(params: list) -> Namespace:
    """
    Set cli args settings to current app running
    and return them as Namespace.
    :param params: list of cli args settings.
    :return: namespace with passed args
    """
    parser = argparse.ArgumentParser()

    for param in params:
        parser.add_argument(*param["names"], **param["kwargs"])

    return parser.parse_args()


def get_args_create_test_logs(path_to_conf: str) -> Namespace:
    """
    Return the Namespace with args for test log creating app
    passed through cli.
    :param path_to_conf: default config file path
    :return: namespace with passed args
    """
    args_params = [
        {
            "names": ("--records", "-r"),
            "kwargs": {
                "help": "Amount of log records in each log file",
                "required": True,
                "type": int,
            },
        },
        {
            "names": ("--cnt", "-c"),
            "kwargs": {
                "help": "Log files quantity",
                "required": True,
                "type": int,
            },
        },
        {
            "names": ("--conf",),
            "kwargs": {
                "help": f"Path to the config file (default: {path_to_conf!r})",
                "required": False,
                "type": str,
                "default": path_to_conf,
            },
        },
    ]
    args = get_parsed_args(args_params)
    return args


def get_args_log_analyzer(path_to_conf: str) -> Namespace:
    """
    Return the Namespace with args for log analyzer app
    passed through cli.
    :param path_to_conf: default config file path
    :return: namespace with passed args
    """
    args_params = [
        {
            "names": ("--conf",),
            "kwargs": {
                "help": f"Path to the config file (default: {path_to_conf!r})",
                "required": False,
                "type": str,
                "default": path_to_conf,
            },
        },
    ]
    args = get_parsed_args(args_params)
    return args
