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
from argparse import Namespace
from collections import namedtuple
from datetime import datetime
from statistics import mean, median
from string import Template
from typing import Any, Dict, Generator, Optional, Tuple, Union

from utils.args_parser import get_args_log_analyzer
from utils.logging_utils import (
    logging_error,
    logging_exception,
    logging_info,
    setup_logging,
)

CONFIG_DEFAULT_PATH = "config.json"
PARSE_ERROR_LIMIT = 0.2

config: Dict[str, Union[int, float, str]] = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "DATA_ENCONDING": "UTF-8",
    "PARSE_ERROR_LIMIT": PARSE_ERROR_LIMIT,
}

LastLogData = namedtuple("LastLogData", "path, date, ext")


def get_config(conf: dict, params: Namespace) -> dict:
    """TODO"""
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        conf[key] = value
    return conf


def search_last_log(conf: dict) -> Optional[LastLogData]:
    """TODO"""
    log_dir = str(conf.get("LOG_DIR"))

    if not os.path.isdir(log_dir):
        raise NotADirectoryError

    res_file_info = None

    for file in os.listdir(log_dir):
        fn_match = re.match(r"^[\w\-.]+(?P<date>\d{8})(?P<ext>.gz|)$", file)
        if fn_match:
            log_date = datetime.strptime(fn_match.group("date"), "%Y%m%d")
            ext = fn_match.group("ext")

            current_file_info = LastLogData(os.path.join(log_dir, file), log_date, ext)
            if res_file_info is None or res_file_info.date < current_file_info.date:
                res_file_info = current_file_info

    if res_file_info:
        report_path = get_report_path(res_file_info.date, conf)
        if os.path.isfile(report_path):
            raise FileExistsError(f"Report file already exists: {str(report_path)!r}")

    return res_file_info


def get_log_data(conf: dict) -> Tuple[LastLogData, list[str]]:
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


def parse_log_data(
    log_file_data: list[str], filepath: str, conf: dict
) -> Generator[Tuple[str, float], None, None]:
    """TODO"""
    logging_info(f"Start parsing log file ({filepath!r}) data...")
    errors_limit = conf.get("PARSE_ERROR_LIMIT") or PARSE_ERROR_LIMIT
    errors_limit = len(log_file_data) * errors_limit
    errors_cnt = 0

    for line in log_file_data:
        line = line.replace('"', "")
        try:
            srch_result = re.search(
                r"^.* (?P<url>/.*) HTTP/1.\d \d{3}.* (?P<time>\d+.\d+)$", line
            )
            if srch_result:
                url = str(srch_result.group("url"))
                time = float(srch_result.group("time"))
            else:
                raise ValueError(f"Can't parse url and time from log string:\n{line}")
        except Exception as e:
            logging_error(f"The error occurred while parsing file {filepath!r}: {e}")
            errors_cnt += 1
            continue

        yield url, time

    if errors_cnt > errors_limit:
        raise ValueError(
            f"Too much errors has occurred while parsing file {filepath!r}"
        )
    else:
        errors_perc = round(errors_cnt / len(log_file_data) * 100, 2)
        errors_percentage_text = (
            f" There were ~{errors_perc}% of errors." if errors_perc else ""
        )
        logging_info(
            f"The file {filepath!r} has been parsed successfully.{errors_percentage_text}"
        )


def prepare_report_data(parsed_data: Generator) -> list[dict]:
    """TODO"""
    logging_info(f"Start preparing report data...")
    urls_data_dict: Dict[str, Any] = {}
    total_time_sum = total_measurments = 0
    for url, time in parsed_data:
        url_measurments = urls_data_dict.get(url)
        if url_measurments:
            url_measurments["series"].append(time)
            url_measurments["time_sum"] += time
        else:
            urls_data_dict[url] = {
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
            urls_data_dict.items(),
        )
    )
    urls_data = sorted(urls_data, key=lambda el: el["time_sum"], reverse=True)
    report_size: int = int(config["REPORT_SIZE"])
    if report_size:
        urls_data = urls_data[:report_size]

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


def get_report_path(report_date: datetime, conf: dict) -> str:
    """TODO"""
    report_fn = f"report-{datetime.strftime(report_date, '%Y.%m.%d')}.html"
    return os.path.join(conf["REPORT_DIR"], report_fn)


def create_report_file(
    report_data: list[dict], report_date: datetime, conf: dict
) -> None:
    """TODO"""
    logging_info("Start report file creating...")
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
    logging_info(f"Finish report file {str(report_path)!r} creating...")


def main(init_config) -> None:
    """TODO"""
    try:
        params = get_args_log_analyzer(CONFIG_DEFAULT_PATH)
        conf = get_config(init_config, params)
        setup_logging(conf)

        logging_info("Log analyzer has been started...")
        log_file_info, log_file_data = get_log_data(conf)
        parsed_data = parse_log_data(log_file_data, log_file_info.path, conf)
        report_data = prepare_report_data(parsed_data)
        create_report_file(report_data, log_file_info.date, conf)
        logging_info("Log analyzer has been successfully finished...")
    except ValueError as e:
        logging_error(f"Warning: {e}")
        sys.exit()
    except KeyboardInterrupt as e:
        logging_exception(f"Process has been interrupted: {e}")
    except BaseException as e:
        logging_exception(f"Error: {e}")


if __name__ == "__main__":  # pragma: no cover
    main(config)
