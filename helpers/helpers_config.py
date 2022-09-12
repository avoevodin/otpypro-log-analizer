import json
from argparse import Namespace

CONFIG_DEFAULT_PATH = "config.json"


def get_config(conf: dict, params: Namespace) -> dict:
    """
    Return dict with app configs, merged from const and the passed config file.
    :param conf: app config
    :param params: params from cli
    :return: dict with app configs
    """
    path_to_conf = params.conf or CONFIG_DEFAULT_PATH
    with open(path_to_conf, "r") as f:
        config_from_file = json.load(f)

    for key, value in config_from_file.items():
        conf[key] = value
    return conf
