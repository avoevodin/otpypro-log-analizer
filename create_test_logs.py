import datetime
import gzip
import os
import random
from argparse import Namespace
from pathlib import Path

from faker import Faker

from utils.args_parser import get_args_create_test_logs
from utils.logging_utils import logging_info, setup_logging

TEST_LOG_DIR = "generated_logs"
LOG_ENC = "UTF-8"
GZ_EXT = ".gz"

fake = Faker()


def clear_test_logs_dir():
    """TODO"""
    logging_info("Start clearing logs directory.")
    for f in os.listdir(TEST_LOG_DIR):
        os.remove(os.path.join(TEST_LOG_DIR, f))
    logging_info("Finish clearing logs directory.")


def create_log_file(fn: str, ext: str, records: list):
    """TODO"""
    f_ext = ext if ext != GZ_EXT else ""
    fn = f"{fn}{f_ext}"
    logging_info(f"Start creating a file '{fn}'")
    f_path = Path(TEST_LOG_DIR, fn)
    with open(f_path, "w", encoding=LOG_ENC) as f:
        f.writelines(records)
    if ext == GZ_EXT:
        logging_info(f"Start compressing the file {fn}")
        f_gz_path = Path(TEST_LOG_DIR, f"{fn}{ext}")
        with open(f_path, "rb") as f, gzip.open(f_gz_path, "wb") as f_gz:
            f_gz.writelines(f)
        os.remove(f_path)
        logging_info(
            f"Compressing the file '{fn}' has been completed. Created '{fn}{ext}' archive."
        )

    logging_info(f"The file '{fn}{ext}' has been created successfully.")


def generate_log_files(logs_data: list[tuple]):
    """TODO"""
    for fn, ext, records in logs_data:
        create_log_file(fn, ext, records)


def generate_log_records(date: datetime, records_cnt: int) -> list[str]:
    """TODO"""
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


def generate_logs_data(days_cnt: int, records_cnt: int) -> list[tuple]:
    """TODO"""
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
                fake.random_element(elements=(".gz", "", ".bz2", ".tar")),
                records,
            )
        )

    return logs_data


def create_logs(params: Namespace):
    """TODO"""
    logging_info("Start logs generation...")
    clear_test_logs_dir()
    cnt = int(params.cnt)
    records = int(params.records)
    logs_data = generate_logs_data(cnt, records)
    generate_log_files(logs_data)
    logging_info("Finish logs generation...")


def main():
    """TODO"""
    setup_logging({})
    args = get_args_create_test_logs()
    create_logs(args)


if __name__ == "__main__":
    main()
