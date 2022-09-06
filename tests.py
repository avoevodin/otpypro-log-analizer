"""
TODO
"""
import argparse
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import TestCase, mock


from utils.logging_utils import setup_logging
from log_analyzer import PARSE_ERROR_LIMIT, get_config


def remove_tmpdir(dir_name: str) -> None:
    """TODO"""
    shutil.rmtree(dir_name)


def create_config_file(filepath: str, encoding: str) -> None:
    """TODO"""
    config_json = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        "LOGS_FILENAME": "log/exec_logs/",
        "LOG_LEVEL": "DEBUG",
        "DATA_ENCONDING": "UTF-8",
        "SOME_OTHER_FLAG": True,
    }
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(config_json, f)


class TestLogAnalyzer(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.base_dir = ".tmp_base_dir"  # tempfile.mkdtemp()
        # self.addCleanup(remove_tmpdir, self.base_dir)
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
        create_config_file(self.config_file_path, self.config["DATA_ENCONDING"])

        self.log_file_path = os.path.join(self.log_dir, "nginx-access-ui.log-20220630")
        self.log_gzip_file_path = os.path.join(self.log_file_path, ".gz")

    def test_config_setup(self) -> None:
        """TODO"""
        with mock.patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(conf=self.config_file_path),
        ):
            conf = get_config()

        self.assertIsInstance(conf, dict)
        self.assertEqual(conf["SOME_OTHER_FLAG"], True)

    def test_search_last_log_file(self) -> None:
        """TODO"""
        pass


if __name__ == "__main__":
    unittest.main()
