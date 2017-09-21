#!./venv/bin/python

"""Configuration handler, first check environ then config file"""

from datetime import timedelta
from os import environ
import logging
from pytimeparse import parse as timeparse
from yaml import load as yaml_load

__all__ = ["TOKEN"]

def parse_bool(data):
    if isinstance(data, bool):
        return data
    if not isinstance(data, str):
        return False
    return data.casefold() in ["yes", "y", "true"]

def parse_config():
    """Parse the environ and the config file to set options in globals"""
    config_file = yaml_load(open("config.yml", "r"))
    config_cast = {}

    for key, value in config_file.items():
        globals()[key] = config_cast.get(key, str)(environ.get(key, value))

if __name__ == "__main__":
    from pprint import pprint
    parse_config()
    pprint({key: value for key, value in globals().items() if key in __all__})

elif "config_parsed" not in globals():
    parse_config()
    globals()["config_parsed"] = True
