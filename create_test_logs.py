import datetime
import gzip
import logging
import os
from argparse import Namespace
from pathlib import Path

from faker import Faker

from utils.args_parser import get_args_create_test_logs
from utils.logging_utils import logging_info

TEST_LOG_DIR = "generated_logs"
LOG_ENC = "UTF-8"
GZ_EXT = ".gz"

fake = Faker()


def clear_test_logs_dir():
    """TODO"""
    logging_info("Start clearing logs directory.")
    for f in os.listdir(TEST_LOG_DIR):
        os.remove(os.path.join(TEST_LOG_DIR, f))
    logging_info("Finish clering logs directory.")


def create_logfile(fn: str, ext: str, records_cnt: int):
    """TODO"""
    f_ext = ext if ext != GZ_EXT else ""
    fn = f"{fn}{f_ext}"
    logging_info(f"Start creating a file '{fn}'")
    f_path = Path(TEST_LOG_DIR, fn)
    with open(f_path, "w", encoding=LOG_ENC) as f:
        f.writelines(
            [
                "nginx-access-ui.log-20220904.gz",
                "nginx-access-ui.log-20220903.tar",
                "nginx-access-ui.log-20220902.tar",
                "nginx-access-ui.log-20220901.gz",
                "nginx-access-ui.log-20220831.tar",
                "nginx-access-ui.log-20220830.bz2",
                "nginx-access-ui.log-20220829.bz2",
                "nginx-access-ui.log-20220828.gz",
                "nginx-access-ui.log-20220827",
                "nginx-access-ui.log-20220826.bz2",
            ]
        )
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


def generate_logs_filenames(days_cnt: int) -> list[tuple]:
    """TODO"""
    base = datetime.datetime.today()
    dates_list = [base - datetime.timedelta(days=x) for x in range(days_cnt)]
    names = map(
        lambda logs_date: (
            f"nginx-access-ui.log-{logs_date.year}{logs_date.month:02d}"
            f"{logs_date.day:02d}"
        ),
        dates_list,
    )
    names_list = []
    for name in names:
        names_list.append(
            (name, fake.random_element(elements=(".gz", "", ".bz2", ".tar")))
        )
    return names_list


def create_logs(params: Namespace):
    """TODO"""
    logging_info("Start logs generation...")
    clear_test_logs_dir()
    cnt = int(params.cnt)
    records = int(params.records)
    filenames = generate_logs_filenames(cnt)
    for fn, ext in filenames:
        create_logfile(fn, ext, records)
    logging_info("Finish logs generation...")


def main():
    """TODO"""
    logging.basicConfig(
        format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level="INFO",
    )
    args = get_args_create_test_logs()
    create_logs(args)


if __name__ == "__main__":
    main()
