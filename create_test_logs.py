import datetime
import gzip
import logging
import os
import random
from argparse import Namespace
from typing import Any, Dict, List, Tuple, Union

from faker import Faker

from helpers.args_parser import get_args_create_test_logs
from helpers.config import get_config
from utils.logging_utils import get_logger_adapter

GZ_EXT = ".gz"
CONFIG_DEFAULT_PATH = "config.json"

config: Dict[str, Union[int, float, str]] = {
    "GENERATED_LOG_DIR": "./generated_logs",
    "DATA_ENCODING": "UTF-8",
}


fake = Faker()

logger_adapter = logging.getLogger()


def clear_test_logs_dir(conf: dict) -> None:
    """
    Clear log dir specified at LOG_DIR setting.
    :param conf: app configs
    :return:
    """
    log_dir = conf["GENERATED_LOG_DIR"]
    logger_adapter.info("Start clearing logs directory.")
    for f in os.listdir(log_dir):
        os.remove(os.path.join(log_dir, f))
    logger_adapter.info("Finish clearing logs directory.")


def create_log_file(fn: str, ext: str, records: List, conf: dict) -> None:
    """
    Create the log file with passed params.
    :param fn: filename
    :param ext: extension of the log file
    :param records: records of the log file
    :param conf: app configs
    :return:
    """
    f_ext = ext if ext != GZ_EXT else ""
    fn = f"{fn}{f_ext}"
    log_dir = conf["GENERATED_LOG_DIR"]
    encoding = conf["DATA_ENCODING"]
    logger_adapter.info(f"Start creating a file '{fn}'")
    f_path = os.path.join(log_dir, fn)
    with open(f_path, "w", encoding=encoding) as f:
        f.writelines(records)
    if ext == GZ_EXT:
        logger_adapter.info(f"Start compressing the file {fn}")
        f_gz_path = os.path.join(log_dir, f"{fn}{ext}")
        with open(f_path, "rb") as f, gzip.open(f_gz_path, "wb") as f_gz:
            f_gz.writelines(f)
        os.remove(f_path)
        logger_adapter.info(
            f"Compressing the file '{fn}' has been completed. Created '{fn}{ext}' archive."
        )

    logger_adapter.info(f"The file '{fn}{ext}' has been created successfully.")


def generate_log_files(logs_data: List[Tuple[str, Any, List[str]]], conf: dict) -> None:
    """
    Generating log files with passed data.
    :param logs_data: log files data
    :param conf: app config
    :return:
    """
    for fn, ext, records in logs_data:
        create_log_file(fn, ext, records, conf)


def generate_log_records(date: datetime.datetime, records_cnt: int) -> List[str]:
    """
    Generate random records for the log file.
    :param date: date of the log file
    :param records_cnt: amount of log records in the file
    :return: list of generated records.
    """
    records = []
    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + datetime.timedelta(days=1, microseconds=-1)
    frm_str = (
        "{remote_addr} {remote_user}  {http_x_real_ip} [{time_local}] "
        '"{request}" {status} {body_bytes_sent} "{http_referer}" '
        '"{http_user_agent}" "{http_x_forwarded_for}" "{http_x_request_id}" '
        '"{http_x_rb_user}" {request_time}\n'
    )

    for _ in range(records_cnt):
        records_data = {
            "remote_addr": fake.ipv4(),
            "remote_user": fake.hexify(text="^" * random.randint(8, 20)),
            "http_x_real_ip": "-",
            "time_local": datetime.datetime.strftime(
                fake.date_time_between(start_date=start_date, end_date=end_date),
                "%d/%b/%Y:%H:%M:%S +0300",
            ),
            "request": f"{fake.http_method()} /{fake.uri_path()} HTTP/1.1",
            "status": fake.random_element(elements=(200, 302, 404)),
            "body_bytes_sent": random.randint(0, 2000),
            "http_referer": "-",
            "http_user_agent": fake.user_agent(),
            "http_x_forwarded_for": "-",
            "http_x_request_id": fake.pystr_format(
                "##########-##########-####-#######"
            ),
            "http_x_rb_user": fake.hexify(text="^" * random.randint(8, 20)),
            "request_time": fake.pyfloat(1, 3, positive=True, max_value=1.2),
        }
        remote_user = records_data["remote_user"]
        records_data["remote_user"] = remote_user if remote_user else "-"
        body_bytes_sent = records_data["body_bytes_sent"]
        records_data["body_bytes_sent"] = body_bytes_sent if body_bytes_sent else "-"
        http_x_rb_user = records_data["http_x_rb_user"]
        records_data["http_x_rb_user"] = http_x_rb_user if http_x_rb_user else "-"

        records.append(frm_str.format(**records_data))

    return records


def generate_logs_data(
    days_cnt: int, records_cnt: int
) -> List[Tuple[str, str, List[str]]]:
    """
    Generate random log files data with passed params.
    :param days_cnt: amount of days should be covered with logs
    :param records_cnt: amount of records in each log file.
    :return: list with tuples (filename, file_extension, log_records)
    """
    base = datetime.datetime.today()
    dates_list = [base - datetime.timedelta(days=x) for x in range(days_cnt)]
    names = map(
        lambda logs_date: (
            f"nginx-access-ui.log-{datetime.datetime.strftime(logs_date, '%Y%m%d')}",
            logs_date,
        ),
        dates_list,
    )
    logs_data = []
    for name, date in names:
        records = generate_log_records(date, records_cnt)
        logs_data.append(
            (
                name,
                str(fake.random_element(elements=(".gz", "", ".bz2", ".tar"))),
                records,
            )
        )

    return logs_data


def create_logs(conf: dict, params: Namespace) -> None:
    """
    Creates random log files.
    :param conf: app config
    of records in each log file.
    :return:
    """
    logger_adapter.info("Start logs generation...")
    clear_test_logs_dir(conf)
    cnt = int(params.cnt)
    records = int(params.records)
    logs_data = generate_logs_data(cnt, records)
    generate_log_files(logs_data, conf)
    logger_adapter.info("Finish logs generation...")


def main(init_config: Dict) -> None:
    """
    Main method of random logs generation app.
    :param init_config: app config
    :return:
    """
    params = get_args_create_test_logs(CONFIG_DEFAULT_PATH)
    conf = get_config(init_config, params)
    create_logs(conf, params)


if __name__ == "__main__":  # pragma: no cover
    main(config)
