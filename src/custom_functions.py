import os
from pathlib import Path
from subprocess import run
from sys import executable as pyexe
from types import SimpleNamespace as Namespace


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

from colorama import Fore, Back, Style


class Console:
    @staticmethod
    def log(message):
        print(f"{Fore.BLACK}{Back.CYAN} INFO {Fore.RESET}{Back.RESET}\t {message}")

    @staticmethod
    def error(message, doexit: bool = False):
        print(f"{Fore.BLACK}{Back.RED} ERROR {Fore.RESET}{Back.RESET}\t {message}")
        if doexit:
            exit(1)

    @staticmethod
    def warn(message):
        print(f"{Fore.BLACK}{Back.YELLOW} WARN {Fore.RESET}{Back.RESET}\t {message}")

    @staticmethod
    def watch(message):
        print(f"{Fore.BLACK}{Back.BLUE} WATCH {Fore.RESET}{Back.RESET}\t {message}")

    @staticmethod
    def dev(message):
        print(
            f"{Fore.BLACK}{Back.LIGHTBLACK_EX} DEV {Fore.RESET}{Back.RESET}\t {message}"
        )

    @staticmethod
    def config(message):
        print(f"{Fore.BLACK}{Back.MAGENTA} CONFIG {Fore.RESET}{Back.RESET} {message}")

    @staticmethod
    def tip(message):
        print(
            f"{Fore.BLACK}{Back.LIGHTYELLOW_EX} TIP {Fore.RESET}{Back.RESET}\t {message}"
        )


console = Console()


def load_json(json_path):
    with open(json_path, "r") as f:
        return ujson.load(f)


def dump_json(json_path, data):
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
    global_location = boulder_path() / "global_config.json"
    if global_location.exists():
        return load_json(global_location)


class Git:
    def __init__(self, repo_url: str, local_path: str):
        self.repo_url = repo_url
        self.local_path = local_path

    def clone(self):
        if not os.path.exists(self.local_path):
            result = run(
                ["git", "clone", self.repo_url, self.local_path],
                capture_output=True,
                text=True,
            )
            if result.stderr == "":
                return Namespace(success=True, output=result.stdout)
            else:
                return Result(success=False, output=result.stderr)
        else:
            console.error(f"{self.local_path} already exists!")
            console.tip("Did you mean to pull?")
            exit(1)

    def pull(self):
        if os.path.exists(self.local_path):
            result = run(
                ["git", "-C", self.local_path, "pull"], capture_output=True, text=True
            )
            if result.stderr == "":
                return Result(success=True, output=result.stdout)
            else:
                return Result(success=False, output=result.stderr)
        else:
            console.error(f"{self.local_path} isn't a valid repo!")
            console.tip("Did you mean to clone?")


def parser(args):
    supported_args = [
        {
            "arg": "build",
            "help": f"Builds the project to your other folder.{Fore.CYAN}This is automatically enabled when running --watch and/or --dev{Fore.RESET}",
        },
        {
            "arg": "dev",
            "help": "Builds and moves the project automatically to the development folder",
        },
        {"arg": "init", "help": "Initialize a Boulder project"},
        {
            "arg": "watch",
            "help": "Watches the project for changes and builds it automatically",
        },
        {"arg": "verbose", "help": "Enable verbose output"},
    ]
