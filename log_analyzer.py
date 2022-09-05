"""
Log analyzer app.
"""

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import datetime
import json
import logging
from pathlib import Path

from utils.args_parser import get_args_log_analyzer
from utils.logging_utils import logging_exception, logging_info, setup_logging

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
}

CONFIG_DEFAULT_PATH = "config.json"


def get_log_data(conf: dict) -> list[str]:
    """TODO"""
    pass


def process_log_data(log_data: list[str], conf: dict) -> (str, bool):
    return "", False


def create_log_report(report_data: str, conf: dict):
    pass


def get_config() -> dict:
    params = get_args_log_analyzer(CONFIG_DEFAULT_PATH)
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        config[key] = value

    return config


def main():
    """TODO"""
    try:
        conf = get_config()
        setup_logging(conf)
        logging_info("Log analyzer has been started...")
        log_data = get_log_data(config)
        report_data, parse_completed = process_log_data(log_data, config)
        if parse_completed:
            create_log_report(report_data, config)
        logging_info("Log analyzer has been successfully finished...")
    except Exception as e:
        logging_exception(e)


if __name__ == "__main__":
    main()
