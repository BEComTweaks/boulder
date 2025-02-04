import os, re, inspect
from pathlib import Path
from subprocess import run as sp_run
from sys import executable as pyexe
from types import SimpleNamespace as Namespace
from typing import Union


def require(module, module_name=""):
    try:
        __import__(module)
    except ImportError:
        try:
            if module_name == "":
                run([pyexe, "-m", "pip", "install", module, "--quiet"])
            else:
                run([pyexe, "-m", "pip", "install", module_name, "--quiet"])
        except KeyboardInterrupt:
            console.error("Keyboard Interrupt", doexit=True)
    except KeyboardInterrupt:
        console.error("Keyboard Interrupt", doexit=True)


require("colorama")
from colorama import *

require("ujson")
import ujson


def get_caller_info():
    frame = inspect.currentframe()
    while frame:
        if frame.f_code.co_filename != __file__:
            return str(frame.f_code.co_filename).split(os.path.sep)[-1], frame.f_lineno
        frame = frame.f_back
    return __file__, 0


def run(command: Union[str, list]):
    try:
        print(
            f"{Fore.BLACK}{Back.LIGHTWHITE_EX} RUN    {Fore.RESET}{Back.RESET} {command if isinstance(command, str) else ' '.join(command)}"
        )
        return sp_run(command, capture_output=True, text=True, shell=True)
    except KeyboardInterrupt:
        console.error("Keyboard Interrupt", doexit=True)


class Console:
    def __init__(self, verbose: bool = False, allow_tips: bool = True):
        self.verbose = verbose
        self.tips = allow_tips

    def _format(self, tag, color, message):
        tag = tag.ljust(6)  # Centers the text inside the tag
        print(f"{Fore.BLACK}{color} {tag} {Fore.RESET}{Back.RESET} {message}")

    def log(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("INFO", Back.CYAN, message)

    def error(self, message, doexit: bool = False, vb: bool = False):
        if (vb and self.verbose) or not vb:
            filename, lineno = get_caller_info()
            self._format("ERROR", Back.RED, f"Line {lineno} in {filename}: {message}")
            if doexit and not (vb and self.verbose):
                exit(1)

    def warn(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            filename, lineno = get_caller_info()
            self._format("WARN", Back.YELLOW, f"Line {lineno} in {filename}: {message}")

    def watch(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("WATCH", Back.BLUE, message)

    def dev(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("DEV", Back.LIGHTBLACK_EX, message)

    def config(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("CONFIG", Back.MAGENTA, message)

    def tip(self, message):
        if self.tips:
            self._format("TIP", Back.LIGHTYELLOW_EX, message)

    def input(self, message):
        return input(
            f"{Fore.BLACK}{Back.LIGHTWHITE_EX} INPUT  {Fore.RESET}{Back.RESET} {message} "
        )


console = Console()

"""
console.log("Log")
console.warn("Warn")
console.watch("Watch")
console.dev("Dev")
console.config("Config")
console.tip("Tip")
console.input("Input")
"""

try:
    require("requests")
    import requests
except KeyboardInterrupt:
    console.error("Keyboard Interrupt", doexit=True)


def load_json(json_path: Union[str, Path]):
    with open(json_path, "r") as f:
        return ujson.load(f)


def dump_json(json_path: Union[str, Path], data: Union[str, Path]):
    with open(json_path, "w") as f:
        ujson.dump(data, f, indent=4)


def project_path():
    return Path(os.getcwd())


def load_boulder_config():
    current_path = project_path()
    while current_path != current_path.parent:
        config_path = current_path / "boulder_config.json"
        if config_path.exists():
            return load_json(config_path)
        current_path = current_path.parent


def boulder_path():
    return Path(__file__).parent


def load_global_config():
    global_location = boulder_path() / "config.json"
    console.log(global_location)
    if global_location.exists():
        return load_json(global_location)


def load_from_remote(pathFromBaseRepo: str, isJson: bool = False):
    # change branch name
    remote_url = "https://raw.githubusercontent.com/BEComTweaks/boulder/refs/heads/im-cooking-please-wait/"
    try:
        response = requests.get(f"{remote_url}{pathFromBaseRepo}")
        if response.status_code == 200:
            if isJson:
                return response.json()
            else:
                return response.text
        else:
            raise requests.exceptions.ConnectionError
    except requests.exceptions.ConnectionError:
        console.error("Could not fetch files from remote!")
        exit(1)


class BuildIssue(Exception):
    pass


def check_branch(result):
    result = result.stdout.split("\n")[0][2:]
    version_match = re.search(r"\(HEAD detached at (v[^)]+)\)", result)
    commit_match = re.search(r"\(HEAD detached at ([^)]+)\)", result)
    if version_match:
        return version_match.group(1)
    elif commit_match:
        return commit_match.group(1)
    else:
        return result
