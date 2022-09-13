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
from statistics import mean, median
from string import Template
from typing import Any, Dict, Generator, Optional, Tuple, Union, List

from config import get_config
from utils.logging_utils import get_logger_adapter

PARSE_ERROR_LIMIT = 0.2

config: Dict[str, Union[int, float, str]] = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "DATA_ENCODING": "UTF-8",
    "PARSE_ERROR_LIMIT": PARSE_ERROR_LIMIT,
}

LastLogData = namedtuple("LastLogData", "path, date, ext")

logger_adapter = get_logger_adapter(__name__, get_config(config))


def search_log_file(conf) -> Optional[LastLogData]:
    """
    Returns last log file by date in the name of log.
    :param conf: app configs
    :return: named tuple (path_to_file, date_in_filename, file_extension)
    """
    logger_adapter.info("Searching last log file...")
    log_dir = str(conf.get("LOG_DIR"))

    if not os.path.isdir(log_dir):
        raise NotADirectoryError

    log_file_info = None

    for file in os.listdir(log_dir):
        fn_match = re.match(r"^[\w\-.]+(?P<date>\d{8})(?P<ext>.gz|)$", file)
        if fn_match:
            log_date = datetime.strptime(fn_match.group("date"), "%Y%m%d")
            ext = fn_match.group("ext")

            current_file_info = LastLogData(os.path.join(log_dir, file), log_date, ext)
            if log_file_info is None or log_file_info.date < current_file_info.date:
                log_file_info = current_file_info

    if log_file_info:
        report_path = get_report_path(log_file_info.date, conf)
        if os.path.isfile(report_path):
            raise FileExistsError(f"Report file already exists: {str(report_path)!r}")

    if log_file_info:
        logger_adapter.info(
            f"Log file {log_file_info.path!r} has been found successfully!"
        )
    else:
        raise FileExistsError(f"Log file hasn't been found!")

    return log_file_info


def get_log_data(log_file_info: LastLogData, conf: dict) -> Generator[str, None, None]:
    """
    Returns records of the log file.
    :param log_file_info: named tuple (path_to_file, date_in_filename, file_extension)
    :param conf: app config
    :return: generator for strings of log file records
    """
    logger_adapter.info(f"Loading the log file {log_file_info.path!r}...")
    open_fn = gzip.open if log_file_info.ext == ".gz" else open
    with open_fn(log_file_info.path, "rb") as fb:
        for line in fb:
            yield line.decode(encoding=conf["DATA_ENCODING"])
    logger_adapter.info(
        f"The file {log_file_info.path!r} has been successfully loaded!"
    )


def parse_log_data(
    log_file_data: Generator[str, None, None], filepath: str, conf: dict
) -> Generator[Tuple[str, float], None, None]:
    """
    Return parsed log file data.
    :param log_file_data: log file data by lines generator
    :param filepath: path to log file
    :param conf: app configs
    :return: generator with url string and request time float number.
    """
    logger_adapter.info(f"Start parsing log file ({filepath!r}) data...")
    errors_limit = conf.get("PARSE_ERROR_LIMIT") or PARSE_ERROR_LIMIT
    total_lines_cnt = 0
    errors_cnt = 0

    for line in log_file_data:
        total_lines_cnt += 1
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
            logger_adapter.error(
                f"The error occurred while parsing file {filepath!r}: {e}"
            )
            errors_cnt += 1
            continue

        yield url, time

    errors_limit = total_lines_cnt * errors_limit
    if errors_cnt > errors_limit:
        raise RuntimeError(
            f"Too much errors has occurred while parsing file {filepath!r}"
        )
    else:
        errors_perc = round(errors_cnt / total_lines_cnt * 100, 2)
        errors_percentage_text = (
            f" There were ~{errors_perc}% of errors." if errors_perc else ""
        )
        logger_adapter.info(
            f"The file {filepath!r} has been parsed successfully.{errors_percentage_text}"
        )


def prepare_report_data(parsed_data: Generator) -> List[dict]:
    """
    Return data prepared for the report with passed log file data.
    :param parsed_data: parsed log file data generator (url, request_time)
    :return: list of a report lines.
    """
    logger_adapter.info(f"Start preparing report data...")
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

    urls_data = [
        {
            "url": data[0],
            "series": data[1]["series"],
            "time_sum": data[1]["time_sum"],
        }
        for data in urls_data_dict.items()
    ]
    urls_data = sorted(urls_data, key=lambda el: el["time_sum"], reverse=True)
    report_size = int(config["REPORT_SIZE"])
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
    logger_adapter.info(f"Report data has been prepared successfully.")
    return report_data


def get_report_path(report_date: datetime, conf: dict) -> str:
    """
    Return report path based on the report date and the REPORT_DIR config.
    :param report_date: date of current report
    :param conf: app configs
    :return: path to report file.
    """
    report_fn = f"report-{datetime.strftime(report_date, '%Y.%m.%d')}.html"
    return os.path.join(conf["REPORT_DIR"], report_fn)


def create_report_file(
    report_data: List[dict], report_date: datetime, conf: dict
) -> None:
    """
    Create report file with passed report data
    :param report_data: list of dicts with the data of report lines
    :param report_date: date of the report
    :param conf: app configs
    :return:
    """
    logger_adapter.info("Start report file creating...")
    report_path = get_report_path(report_date, conf)
    with open(
        "templates/report.html", "r", encoding=conf["DATA_ENCODING"]
    ) as report_template:
        with open(report_path, "w", encoding=conf["DATA_ENCODING"]) as report:
            report_str_template = Template(report_template.read())
            report_str = report_str_template.safe_substitute(
                table_json=json.dumps(report_data)
            )
            report.write(report_str)
    logger_adapter.info(f"Finish report file {str(report_path)!r} creating...")


def main(init_config) -> None:
    """
    Main method of the Log Analyzer.
    :param init_config: app configs
    :return:
    """
    try:

        conf = get_config(init_config)

        logger_adapter.info("Log analyzer has been started...")
        log_file_info = search_log_file(conf)
        log_file_data = get_log_data(log_file_info, conf)
        parsed_data = parse_log_data(log_file_data, log_file_info.path, conf)
        report_data = prepare_report_data(parsed_data)
        create_report_file(report_data, log_file_info.date, conf)
        logger_adapter.info("Log analyzer has been successfully finished...")
    except RuntimeError as e:
        logger_adapter.error(f"Warning: {e}")
        sys.exit()
    except FileExistsError as e:
        logger_adapter.info(f"Warning: {e}")
    except KeyboardInterrupt as e:
        logger_adapter.exception(f"Process has been interrupted: {e}")
    except BaseException as e:
        logger_adapter.exception(f"Error: {e}")


if __name__ == "__main__":  # pragma: no cover
    main(config)
