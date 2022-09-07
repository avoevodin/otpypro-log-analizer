"""
TODO
"""
import argparse
import datetime
import json
import os
import shutil
import tempfile
import unittest
from typing import List
from unittest import TestCase, mock

import create_test_logs
from create_test_logs import create_log_file
from log_analyzer import (
    PARSE_ERROR_LIMIT,
    get_config,
    search_last_log,
    LastLogData,
    get_log_data,
    get_report_path,
)

TEST_STR = "test str\n" * 4


def remove_tmpdir(dir_name: str) -> None:
    """TODO"""
    shutil.rmtree(dir_name)


def get_str_list_fixture() -> List[str]:
    """TODO"""
    return list(map(lambda e: f"{e}\n", TEST_STR.split("\n")[:-1]))


def create_config_file(filepath: str, encoding: str) -> None:
    """TODO"""
    config_json = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        "LOGS_FILENAME": None,
        "LOG_LEVEL": "DEBUG",
        "DATA_ENCONDING": "UTF-8",
        "SOME_OTHER_FLAG": True,
    }
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(config_json, f)


def generate_log_files(log_dir: str, ext: str = "") -> LastLogData:
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
        with mock.patch("create_test_logs.TEST_LOG_DIR", log_dir):
            create_log_file(fn, f_ext, records)

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
        super().setUp()
        self.base_dir = tempfile.mkdtemp()
        # self.base_dir = ".tmp_base_dir"
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
        self.encoding = self.config["DATA_ENCONDING"]
        create_config_file(self.config_file_path, self.encoding)

        self.log_file_path = os.path.join(self.log_dir, "nginx-access-ui.log-20220630")
        self.log_gzip_file_path = os.path.join(self.log_file_path, ".gz")

        self.generate_log_enc_patch = mock.patch(
            "create_test_logs.LOG_ENC", self.encoding
        )
        self.generate_log_enc_patch.start()

    def test_config_setup(self) -> None:
        """TODO"""
        with mock.patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(conf=self.config_file_path),
        ):
            conf = get_config()

        self.assertIsInstance(conf, dict)
        self.assertEqual(conf["SOME_OTHER_FLAG"], True)

    def test_search_last_log_file_with_wrong_log_dir(self) -> None:
        """TODO"""
        self.config["LOG_DIR"] = "foo"
        self.assertRaises(NotADirectoryError, search_last_log, self.config)

    def test_search_last_log_file_report_exist(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.log_dir)
        generate_report(self.config, self.encoding, log_file_info_fixture)
        self.assertRaises(FileExistsError, search_last_log, self.config)

    def test_get_log_data(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.log_dir)
        log_file_info, f_lines = get_log_data(self.config)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        self.assertEqual(f_lines, res_fixture)

    def test_get_log_data_gzip(self) -> None:
        """TODO"""
        log_file_info_fixture = generate_log_files(self.log_dir, ".gz")
        log_file_info, f_lines = get_log_data(self.config)
        print("fixt_info", log_file_info_fixture)
        print("info", log_file_info)
        self.assertEqual(log_file_info.date, log_file_info_fixture.date)
        self.assertEqual(log_file_info.path, log_file_info_fixture.path)
        self.assertEqual(log_file_info.ext, log_file_info_fixture.ext)

        res_fixture = get_str_list_fixture()
        self.assertEqual(f_lines, res_fixture)

    def test_get_log_data_no_log_data(self) -> None:
        """TODO"""
        self.assertRaises(ValueError, get_log_data, self.config)


if __name__ == "__main__":
    unittest.main()
