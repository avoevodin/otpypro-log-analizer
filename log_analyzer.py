"""
Log analyzer app.
"""

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import gzip
import json
import os
import re
import sys
from collections import namedtuple
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import TextIO

from utils.args_parser import get_args_log_analyzer
from utils.logging_utils import (
    logging_exception,
    setup_logging,
    logging_info,
    logging_error,
    logging_warning,
)

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
}

CONFIG_DEFAULT_PATH = "config.json"


def get_config() -> dict:
    """TODO"""
    params = get_args_log_analyzer(CONFIG_DEFAULT_PATH)
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        config[key] = value

    return config


def search_last_log(log_dir: str) -> namedtuple:
    """TODO"""
    if not os.path.isdir(log_dir):
        raise NotADirectoryError

    LastLogData = namedtuple("LastLogData", "path, date, ext")

    res_file_data = None

    for file in os.listdir(log_dir):
        if re.match(r"^[\w\-.]+\d{8}(.gz|)$", file):
            log_date = datetime.strptime(re.search(r"\d{8}", file).group(0), "%Y%m%d")
            ext_res = re.search(r"^.*\d{8}(\.\w+)$", file)
            ext = ""
            if ext_res:
                ext = ext_res.group(1)

            current_file_data = LastLogData(str(Path(log_dir, file)), log_date, ext)
            if res_file_data is None or res_file_data.date < current_file_data.date:
                res_file_data = current_file_data

    return res_file_data


def get_log_data(conf: dict) -> (namedtuple, list[str]):
    """TODO"""
    logging_info("Searching last log file...")
    log_file_info = search_last_log(conf.get("LOG_DIR"))
    logging_info(f"Log file {log_file_info.path!r} has been found successfully!")

    logging_info(f"Loading the log file {log_file_info.path!r}...")
    if log_file_info.ext:
        with gzip.open(log_file_info.path, "rb") as fb:
            f_lines = list(
                map(
                    lambda line: line.decode(encoding=conf["DATA_ENCONDING"]),
                    fb.readlines(),
                )
            )
    else:
        with open(log_file_info.path, "r", encoding=conf["DATA_ENCONDING"]) as f:
            f_lines = f.readlines()
    logging_info(f"The file {log_file_info.path!r} has been successfully loaded!")
    return log_file_info, f_lines


def parse_log_data(log_data: list[str], conf: dict) -> (str, bool):
    """TODO"""
    return "", True


def create_log_report(report_data: str, conf: dict):
    """TODO"""
    pass


def main():
    """TODO"""
    try:
        conf = get_config()
        setup_logging(conf)
        logging_info("Log analyzer has been started...")
        log_file_info, log_file_data = get_log_data(config)

        report_data, parsing_completed = parse_log_data(log_data, config)
        if parsing_completed:
            create_log_report(report_data, config)
        else:
            raise ValueError("Too much errors while parsing!")

        logging_info("Log analyzer has been successfully finished...")
    except ValueError as e:
        logging_exception(f"Error:\n{e}")
        sys.exit()
    except Exception as e:
        logging_exception(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
