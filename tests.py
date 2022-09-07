"""
TODO
"""
import argparse
import datetime
import json
import os
import re
import shutil
import tempfile
import unittest
from typing import List, Tuple
from unittest import TestCase, mock

from create_test_logs import create_log_file
from create_test_logs import main as create_test_logs_main
from log_analyzer import (
    PARSE_ERROR_LIMIT,
    LastLogData,
    get_config,
    get_log_data,
    get_report_path,
)
from log_analyzer import main as log_analyzer_main
from log_analyzer import parse_log_data, prepare_report_data, search_last_log

TEST_STR = "test str\n" * 4


def remove_tmpdir(dir_name: str) -> None:
    """TODO"""
    shutil.rmtree(dir_name)


def get_str_list_fixture() -> List[str]:
    """TODO"""
    return list(map(lambda e: f"{e}\n", TEST_STR.split("\n")[:-1]))


def get_log_file_text_fixture() -> Tuple[str, dict, List[dict]]:
    """TODO"""
    log_text = (
        '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" '
        '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" '
        '"dc7161be3" 0.390\n '
        '1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET '
        '/api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" '
        '"1498697422-32900793-4708-9752770" "-" 0.133\n '
        '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" '
        '"Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199\n '
        '1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" '
        '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" '
        '"2a828197ae235b0b3cb" 0.704\n '
        '1.168.65.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/internal/banner/24294027/info HTTP/1.1" 200 407 '
        '"-" "-" "-" "1498697422-2539198130-4709-9928846" "89f7f1be37d" 0.146\n '
    )
    parse_result_fixture = {
        "/api/v2/banner/25019354": 0.39,
        "/api/1/photogenic_banners/list/?server_name=WIN7RB4": 0.133,
        "/api/v2/banner/16852664": 0.199,
        "/api/v2/slot/4705/groups": 0.704,
        "/api/v2/internal/banner/24294027/info": 0.146,
    }
    report_data_fixture = [
        {
            "url": "/api/v2/slot/4705/groups",
            "count": 1,
            "count_perc": 20.0,
            "time_sum": 0.704,
            "time_perc": 44.784,
            "time_avg": 0.704,
            "time_max": 0.704,
            "time_med": 0.704,
        },
        {
            "url": "/api/v2/banner/25019354",
            "count": 1,
            "count_perc": 20.0,
            "time_sum": 0.39,
            "time_perc": 24.809,
            "time_avg": 0.39,
            "time_max": 0.39,
            "time_med": 0.39,
        },
        {
            "url": "/api/v2/banner/16852664",
            "count": 1,
            "count_perc": 20.0,
            "time_sum": 0.199,
            "time_perc": 12.659,
            "time_avg": 0.199,
            "time_max": 0.199,
            "time_med": 0.199,
        },
        {
            "url": "/api/v2/internal/banner/24294027/info",
            "count": 1,
            "count_perc": 20.0,
            "time_sum": 0.146,
            "time_perc": 9.288,
            "time_avg": 0.146,
            "time_max": 0.146,
            "time_med": 0.146,
        },
        {
            "url": "/api/1/photogenic_banners/list/?server_name=WIN7RB4",
            "count": 1,
            "count_perc": 20.0,
            "time_sum": 0.133,
            "time_perc": 8.461,
            "time_avg": 0.133,
            "time_max": 0.133,
            "time_med": 0.133,
        },
    ]

    return log_text, parse_result_fixture, report_data_fixture


def create_config_file(filepath: str, encoding: str) -> None:
    """TODO"""
    config_json = {
        "REPORT_SIZE": 1000,
        "LOGS_FILENAME": "exec_logs",
        "LOG_LEVEL": "DEBUG",
        "DATA_ENCONDING": "UTF-8",
        "SOME_OTHER_FLAG": True,
    }
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(config_json, f)


def generate_log_files(conf: dict, log_dir: str, ext: str = "") -> LastLogData:
    """TODO"""
    test_string_list = get_str_list_fixture()
    log_files_info = [
        ("nginx-access-ui.log-20220828.bz2", "", test_string_list),
        ("nginx-access-ui.log-20220829.gz", "", test_string_list),
        ("nginx-access-ui.log-20220830.bz2", "", test_string_list),
        (f"nginx-access-ui.log-20220831", ext, test_string_list),
        ("nginx-access-ui.log-20220901.tar", "", test_string_list),
        ("nginx-access-ui.log-20220902.tar", "", test_string_list),
        ("nginx-access-ui.log-20220903.bz2", "", test_string_list),
        ("nginx-access-ui.log-20220904.tar", "", test_string_list),
        ("nginx-access-ui.log-20220905.bz2", "", test_string_list),
        ("nginx-access-ui.log-20220906.tar", "", test_string_list),
    ]
    for fn, f_ext, records in log_files_info:
        create_log_file(fn, f_ext, records, conf)

    return LastLogData(
        path=os.path.join(log_dir, f"nginx-access-ui.log-20220831{ext}"),
        date=datetime.datetime(2022, 8, 31),
        ext=ext,
    )


def generate_report(config: dict, encoding: str, log_file_info: LastLogData) -> None:
    """TODO"""
    rep_path = get_report_path(log_file_info.date, config)
    with open(rep_path, "w", encoding=encoding) as f:
        f.write(TEST_STR)


class TestLogAnalyzer(TestCase):
    def setUp(self) -> None:
        """TODO"""
        super().setUp()
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(remove_tmpdir, self.base_dir)
        self.log_dir = tempfile.mkdtemp(prefix="log_", dir=self.base_dir)
        self.rep_dir = tempfile.mkdtemp(prefix="rep_", dir=self.base_dir)

        self.config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": self.rep_dir,
            "LOG_DIR": self.log_dir,
            "DATA_ENCONDING": "UTF-8",
            "PARSE_ERROR_LIMIT": PARSE_ERROR_LIMIT,
            "LOGS_FILENAME": os.path.join(self.log_dir, "exec_logs"),
            "LOG_LEVEL": "DEBUG",
        }

        self.config_file_path = os.path.join(self.base_dir, "config.json")
        self.encoding = str(self.config["DATA_ENCONDING"])
        create_config_file(self.config_file_path, self.encoding)

        self.conf = get_config(
            self.config, argparse.Namespace(conf=self.config_file_path)
        )

        self.log_file_path = os.path.join(self.log_dir, "nginx-access-ui.log-20220630")
        self.log_gzip_file_path = os.path.join(self.log_file_path, ".gz")

    def test_config_setup(self) -> None:
        """TODO"""
        self.assertIsInstance(self.conf, dict)
        self.assertEqual(self.conf["SOME_OTHER_FLAG"], True)
        self.assertEqual(self.conf["REPORT_DIR"], self.rep_dir)
        self.assertEqual(self.conf["LOG_DIR"], self.log_dir)

    def test_search_last_log_file_with_wrong_log_dir(self) -> None:
        """TODO"""
        self.conf["LOG_DIR"] = "foo"
        self.assertRaises(NotADirectoryError, search_last_log, self.conf)

    def test_search_last_log_file_report_exist(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir)
        generate_report(self.conf, self.encoding, log_file_info_fixture)
        self.assertRaises(FileExistsError, search_last_log, self.conf)

    def test_get_log_data(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir)
        log_file_info, f_lines = get_log_data(self.conf)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        self.assertEqual(f_lines, res_fixture)

    def test_get_log_data_gzip(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir, ".gz")
        log_file_info, f_lines = get_log_data(self.conf)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        self.assertEqual(f_lines, res_fixture)

    def test_get_log_data_no_log_data(self) -> None:
        """TODO"""
        self.assertRaises(ValueError, get_log_data, self.conf)

    def test_parse_log_data(self) -> None:
        """TODO"""
        log_text, result_fixture, _ = get_log_file_text_fixture()
        records = log_text.split("\n")

        result_gen = parse_log_data(records, "test_file_path", self.conf)
        result = {}
        for url, time in result_gen:
            result[url] = time

        self.assertEqual(result_fixture, result)

    def test_parse_not_valid_data(self) -> None:
        """TODO"""
        records = get_str_list_fixture()
        res_gen = parse_log_data(records, "test_file_path", self.conf)
        self.assertRaises(ValueError, next, res_gen)

    def test_prepare_report_data(self) -> None:
        """TODO"""
        log_text, _, report_data_fxt = get_log_file_text_fixture()
        records = log_text.split("\n")
        parsed_data = parse_log_data(records, "test_file_path", self.conf)
        report_data = prepare_report_data(parsed_data)
        self.assertEqual(report_data, report_data_fxt)

    def test_main(self) -> None:
        """TODO"""
        with mock.patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                cnt=10, records=100, conf=self.config_file_path
            ),
        ):
            create_test_logs_main(self.conf)
            log_analyzer_main(self.conf)
            rep_filenames = []
            for _, _, files in os.walk(self.rep_dir):
                for name in files:
                    print(name)
                    if re.match(r"^report-\d{4}.\d{2}.\d{2}.html$", name):
                        rep_filenames.append(name)
            self.assertEqual(len(rep_filenames), 1)


if __name__ == "__main__":
    unittest.main()
