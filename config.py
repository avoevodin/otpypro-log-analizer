import json
from argparse import Namespace

from utils.args_parser import get_args_log_analyzer

CONFIG_DEFAULT_PATH = "config.json"


def get_config(conf: dict) -> dict:
    """
    Return dict with app configs, merged from const and the passed config file.
    :param conf: app config
    :return: dict with app configs
    """
    params = get_args_log_analyzer(CONFIG_DEFAULT_PATH)
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        conf[key] = value
    return conf
