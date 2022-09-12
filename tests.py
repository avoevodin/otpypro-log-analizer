"""
Tests for Log Analyzer app.
"""
import argparse
import datetime
import json
import logging
import os
import re
import shutil
import tempfile
import unittest
from typing import List, Tuple
from unittest import TestCase, mock

with mock.patch(
    "argparse.ArgumentParser.parse_args",
    return_value=argparse.Namespace(cnt=10, records=100, conf=None),
), mock.patch(
    "utils.logging_utils.get_logger_adapter", return_value=logging.getLogger()
):
    from create_test_logs import main as create_test_logs_main, create_log_file
    from config import get_config

    from log_analyzer import (
        PARSE_ERROR_LIMIT,
        LastLogData,
        get_log_data,
        get_report_path,
        search_log_file,
        main as log_analyzer_main,
        parse_log_data,
        prepare_report_data,
        search_last_log,
    )


TEST_STR = "test str\n" * 4


def remove_tmpdir(dir_name: str) -> None:  # pragma: no cover
    """
    Delete temp dir with dir_name.
    :param dir_name: dir name.
    :return:
    """
    shutil.rmtree(dir_name)


def get_str_list_fixture() -> List[str]:  # pragma: no cover
    """
    Returns list of TEST_STR text lines.
    :return: list of test text lines.
    """
    return list(map(lambda e: f"{e}\n", TEST_STR.split("\n")[:-1]))


def get_log_file_text_fixture() -> Tuple[str, dict, List[dict]]:  # pragma: no cover
    """
    Returns fixtures of the test log file.
    :return: tuple with (log_text, parse_result_dict, list_of_report_data_dict)
    """
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


def create_config_file(filepath: str, encoding: str) -> None:  # pragma: no cover
    """
    Create test config json file.
    :param filepath: path to config file
    :param encoding: encoding of config file
    :return:
    """
    config_json = {
        "REPORT_SIZE": 1000,
        "LOGS_FILENAME": None,
        "LOG_LEVEL": "DEBUG",
        "DATA_ENCODING": "UTF-8",
        "SOME_OTHER_FLAG": True,
    }
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(config_json, f)


def generate_log_files(
    conf: dict, log_dir: str, ext: str = ""
) -> LastLogData:  # pragma: no cover
    """
    Generate some dummy log files with passed params.
    :param conf: app config
    :param log_dir: directory for generated log files
    :param ext: extension for the last log file.
    :return: named tuple with fixture log data
    (path_to_file, date_in_filename, file_extension)
    """
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


def generate_report(
    conf: dict, encoding: str, log_file_info: LastLogData
) -> None:  # pragma: no cover
    """
    Generate fake report.
    :param conf: app config
    :param encoding: encoding of report file
    :param log_file_info: info of the log file as named tuple
    (path_to_file, date_in_filename, file_extension)
    :return:
    """
    rep_path = get_report_path(log_file_info.date, conf)
    with open(rep_path, "w", encoding=encoding) as f:
        f.write(TEST_STR)


class TestLogAnalyzer(TestCase):  # pragma: no cover
    def setUp(self) -> None:
        """
        Setup method for Log Analyzer test class.
        :return:
        """
        super().setUp()
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(remove_tmpdir, self.base_dir)
        self.log_dir = tempfile.mkdtemp(prefix="log_", dir=self.base_dir)
        self.rep_dir = tempfile.mkdtemp(prefix="rep_", dir=self.base_dir)

        self.config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": self.rep_dir,
            "LOG_DIR": self.log_dir,
            "DATA_ENCODING": "UTF-8",
            "PARSE_ERROR_LIMIT": PARSE_ERROR_LIMIT,
            "LOGS_FILENAME": os.path.join(self.log_dir, "exec_logs"),
            "LOG_LEVEL": "DEBUG",
            "GENERATED_LOG_DIR": self.log_dir,
        }

        self.config_file_path = os.path.join(self.base_dir, "config.json")
        self.encoding = str(self.config["DATA_ENCODING"])
        create_config_file(self.config_file_path, self.encoding)
        with mock.patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                cnt=10, records=100, conf=self.config_file_path
            ),
        ):
            self.conf = get_config(self.config)

        self.log_file_path = os.path.join(self.log_dir, "nginx-access-ui.log-20220630")
        self.log_gzip_file_path = os.path.join(self.log_file_path, ".gz")

    def test_config_setup(self) -> None:
        """
        Test config setting up with merging config file and const.
        :return:
        """
        self.assertIsInstance(self.conf, dict)
        self.assertEqual(self.conf["SOME_OTHER_FLAG"], True)
        self.assertEqual(self.conf["REPORT_DIR"], self.rep_dir)
        self.assertEqual(self.conf["LOG_DIR"], self.log_dir)

    def test_search_last_log_file_with_wrong_log_dir(self) -> None:
        """
        Test last log file searching with invalid log dir.
        :return:
        """
        self.conf["LOG_DIR"] = "foo"
        self.assertRaises(NotADirectoryError, search_last_log, self.conf)

    def test_generate_report_while_report_exist(self) -> None:
        """
        Test report generating while report exists.
        :return:
        """
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir)
        generate_report(self.conf, self.encoding, log_file_info_fixture)
        self.assertRaises(FileExistsError, search_last_log, self.conf)

    def test_get_log_data(self) -> None:
        """
        Test getting last log file data.
        :return:
        """
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir)
        log_file_info = search_log_file(self.conf)
        log_file_data = get_log_data(log_file_info, self.conf)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        for line, fixt_line in zip(log_file_data, res_fixture):
            self.assertEqual(line, fixt_line)

    def test_get_log_data_gzip(self) -> None:
        """
        Test getting last log gzip file data.
        :return:
        """
        log_file_info_fixture = generate_log_files(self.conf, self.log_dir, ".gz")
        log_file_info = search_log_file(self.conf)
        log_file_data = get_log_data(log_file_info, self.conf)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        for line, fixt_line in zip(log_file_data, res_fixture):
            self.assertEqual(line, fixt_line)

    def test_get_log_data_no_log_data(self) -> None:
        """
        Test getting log data with no log files.
        :return:
        """
        self.assertRaises(FileExistsError, search_log_file, self.conf)

    def test_parse_log_data(self) -> None:
        """
        Test parsing log file data.
        :return:
        """
        log_text, result_fixture, _ = get_log_file_text_fixture()
        records = (line for line in log_text.split("\n"))

        result_gen = parse_log_data(records, "test_file_path", self.conf)
        result = {}
        for url, time in result_gen:
            result[url] = time

        self.assertEqual(result_fixture, result)

    def test_parse_not_valid_data(self) -> None:
        """
        Test parsing not valid log file data.
        :return:
        """
        records = (line for line in get_str_list_fixture())
        res_gen = parse_log_data(records, "test_file_path", self.conf)
        self.assertRaises(ValueError, next, res_gen)

    def test_prepare_report_data(self) -> None:
        """
        Test preparing report data.
        :return:
        """
        log_text, _, report_data_fxt = get_log_file_text_fixture()
        records = (line for line in log_text.split("\n"))
        parsed_data = parse_log_data(records, "test_file_path", self.conf)
        report_data = prepare_report_data(parsed_data)
        self.assertEqual(report_data, report_data_fxt)

    def test_main(self) -> None:
        """
        Test main method of the Log Analyzer.
        :return:
        """
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
