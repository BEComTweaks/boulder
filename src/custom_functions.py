import os
from pathlib import Path
from subprocess import run
from sys import executable as pyexe


def require(module, module_name=""):
    try:
        __import__(module)
    except ImportError:
        if module_name == "":
            run([pyexe, "-m", "pip", "install", module, "--quiet"])
        else:
            run([pyexe, "-m", "pip", "install", module_name, "--quiet"])


require("colorama")
from colorama import *

require("ujson")
import ujson


def print_tag(tag, message):
    if tag == "error":
        print(f"{Back.RED} ERROR {Back.RESET}\t{message}")
    elif tag == "watch":
        print(f"{Back.BLUE} WATCH {Back.RESET}\t{message}")
    elif tag == "dev":
        print(f"{Back.LIGHTBLACK_EX} DEV {Back.RESET}\t{message}")
    elif tag == "warn":
        print(f"{Back.YELLOW} WARN {Back.RESET}\t{message}")


def load_json(json_path):
    with open(json_path, "r") as f:
        return ujson.load(f)


def dump_json(json_path, data):
    with open(json_path, "w") as f:
        ujson.dump(data, f, indent=4)


def load_boulder_config():
    current_path = Path(os.getcwd())
    while current_path != current_path.parent:
        config_path = current_path / "boulder_config.json"
        if config_path.exists():
            return load_json(config_path)
        current_path = current_path.parent


def load_global_config():
    global_location = Path(__file__).parent / "global_config.json"
    if global_location.exists():
        return load_json(global_location)
