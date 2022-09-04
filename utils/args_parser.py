"""
Parse args passed to cli
"""

import argparse
from argparse import Namespace


def get_parsed_args(params: list) -> Namespace:
    """TODO"""
    parser = argparse.ArgumentParser()

    for param in params:
        parser.add_argument(*param["names"], **param["kwargs"])

    return parser.parse_args()


def get_args_create_test_logs() -> Namespace:
    """TODO"""
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
    ]
    args = get_parsed_args(args_params)
    return args


if __name__ == "__main__":
    get_args_create_test_logs()
