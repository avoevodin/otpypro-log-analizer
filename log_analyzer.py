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
from pathlib import Path
from statistics import mean, median
from string import Template
from typing import Generator

from utils.args_parser import get_args_log_analyzer
from utils.logging_utils import (
    logging_exception,
    setup_logging,
    logging_info,
    logging_warning,
)

CONFIG_DEFAULT_PATH = "config.json"
PARSE_ERROR_LIMIT = 0.2

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "DATA_ENCONDING": "UTF-8",
    "PARSE_ERROR_LIMIT": PARSE_ERROR_LIMIT,
}


def get_config() -> dict:
    """TODO"""
    params = get_args_log_analyzer(CONFIG_DEFAULT_PATH)
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        config[key] = value

    return config


def search_last_log(conf: dict) -> namedtuple:
    """TODO"""
    log_dir = conf.get("LOG_DIR")

    if not os.path.isdir(log_dir):
        raise NotADirectoryError

    LastLogData = namedtuple("LastLogData", "path, date, ext")

    res_file_info = None

    for file in os.listdir(log_dir):
        if re.match(r"^[\w\-.]+\d{8}(.gz|)$", file):
            log_date = datetime.strptime(re.search(r"\d{8}", file).group(0), "%Y%m%d")
            ext_res = re.search(r"^.*\d{8}(\.\w+)$", file)
            ext = ""
            if ext_res:
                ext = ext_res.group(1)

            current_file_info = LastLogData(str(Path(log_dir, file)), log_date, ext)
            if res_file_info is None or res_file_info.date < current_file_info.date:
                res_file_info = current_file_info

    if res_file_info:
        report_path = get_report_path(res_file_info.date, conf)
        if os.path.isfile(report_path):
            raise FileExistsError(f"Report file already exists: {str(report_path)!r}")

    return res_file_info


def get_log_data(conf: dict) -> (namedtuple, list[str]):
    """TODO"""
    logging_info("Searching last log file...")
    log_file_info = search_last_log(conf)

    if log_file_info:
        logging_info(f"Log file {log_file_info.path!r} has been found successfully!")
    else:
        raise ValueError(f"Log file hasn't been found!")

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


def parse_log_data(log_file_data: list[str], filepath: str, conf: dict) -> (str, bool):
    """TODO"""
    logging_info(f"Start parsing log file ({filepath!r}) data...")
    errors_limit = conf.get("PARSE_ERROR_LIMIT") or PARSE_ERROR_LIMIT
    errors_limit = len(log_file_data) * errors_limit
    errors_cnt = 0

    for line in log_file_data:
        line = line.replace('"', "")
        try:
            srch_result = re.search(
                r"^.* (?P<url>/.+) HTTP/1.\d \d{3}.* (?P<time>\d+.\d+)$", line
            )
            url = srch_result.group("url")
            time = float(srch_result.group("time"))
        except Exception as e:
            logging_warning(f"The error occurred while parsing file {filepath!r}: {e}")
            errors_cnt += 1
            continue

        yield url, time

    if errors_cnt > errors_limit:
        raise ValueError(
            f"Too much errors has occurred while parsing file {filepath!r}"
        )
    else:
        errors_percentage_text = (
            f" There were {errors_cnt/len(log_file_data)}% of errors."
            if errors_cnt
            else ""
        )
        logging_info(
            f"The file {filepath!r} has been parsed successfully.{errors_percentage_text}"
        )


def prepare_report_data(parsed_data: Generator) -> list[dict]:
    """TODO"""
    logging_info(f"Start preparing report data...")
    urls_data = {}
    total_time_sum = total_measurments = 0
    for url, time in parsed_data:
        url_measurments = urls_data.get(url)
        if url_measurments:
            url_measurments["series"].append(time)
            url_measurments["time_sum"] += time
        else:
            urls_data[url] = {
                "series": [time],
                "time_sum": time,
            }
        total_time_sum += time
        total_measurments += 1

    urls_data = list(
        map(
            lambda data: {
                "url": data[0],
                "series": data[1]["series"],
                "time_sum": data[1]["time_sum"],
            },
            urls_data.items(),
        )
    )
    urls_data = sorted(urls_data, key=lambda el: el["time_sum"], reverse=True)
    urls_data = urls_data[: config["REPORT_SIZE"]]

    report_data = []
    for url_data in urls_data:
        url, series, time_sum = url_data.values()
        report_data.append(
            {
                "url": url,
                "count": len(series),
                "count_perc": round(len(series) / total_measurments * 100, 3),
                "time_sum": round(time_sum, 3),
                "time_perc": round(time_sum / total_time_sum * 100, 3),
                "time_avg": round(mean(series), 3),
                "time_max": round(max(series), 3),
                "time_med": round(median(series), 3),
            }
        )
    logging_info(f"Report data has been prepared successfully.")
    return report_data


def get_report_path(report_date: datetime, conf: dict) -> Path:
    """TODO"""
    report_fn = f"report-{datetime.strftime(report_date, '%Y.%m.%d')}.html"
    return Path(conf["REPORT_DIR"], report_fn)


def create_report_file(
    report_data: list[dict], report_date: datetime, conf: dict
) -> None:
    """TODO"""
    report_path = get_report_path(report_date, conf)
    with open(
        "templates/report.html", "r", encoding=conf["DATA_ENCONDING"]
    ) as report_template:
        with open(report_path, "w", encoding=conf["DATA_ENCONDING"]) as report:
            report_str_template = Template(report_template.read())
            report_str = report_str_template.safe_substitute(
                table_json=json.dumps(report_data)
            )
            report.write(report_str)


def main() -> None:
    """TODO"""
    try:
        conf = get_config()
        setup_logging(conf)

        logging_info("Log analyzer has been started...")
        log_file_info, log_file_data = get_log_data(conf)
        parsed_data = parse_log_data(log_file_data, log_file_info.path, conf)
        report_data = prepare_report_data(parsed_data)
        create_report_file(report_data, log_file_info.date, conf)

        logging_info("Log analyzer has been successfully finished...")
    except ValueError as e:
        logging_warning(f"Warning: {e}")
        sys.exit()
    except FileExistsError as e:
        logging_warning(f"Warning: {e}")
    except Exception as e:
        logging_exception(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
