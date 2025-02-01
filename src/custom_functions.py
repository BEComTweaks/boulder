import os
from pathlib import Path
from subprocess import run
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

    @staticmethod
    def input(message):
        return input(
            f"{Fore.BLACK}{Back.LIGHTWHITE_EX} INPUT {Fore.RESET}{Back.RESET}\t {message}"
        )

console = Console()
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
    global_location = boulder_path() / "global_config.json"
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
                return Namespace(success=False, output=result.stderr)
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
                return Namespace(success=True, output=result.stdout)
            else:
                return Namespace(success=False, output=result.stderr)
        else:
            console.error(f"{self.local_path} isn't a valid repo!")
            console.tip("Did you mean to clone?")


def parser(args):
    arguments = [
        f"Boulder: {Fore.GREEN}Regolith, built with Python{Fore.RESET}",
        {
            "arg": "build",
            "help": f"Builds the project to your other folder. {Fore.CYAN}This is automatically enabled when running --watch and/or --dev{Fore.RESET}",
            "action": "store_true",
        },
        {
            "arg": "dev",
            "help": "Builds and moves the project automatically to the development folder",
            "action": "store_true",
        },
        {"arg": "init", "help": "Initialize a Boulder project", "action": "store_true"},
        {
            "arg": "watch",
            "help": "Watches the project for changes and builds it automatically",
            "action": "store_true",
        },
        {"arg": "verbose", "help": "Enable verbose output", "action": "store_true"},
        {
            "arg": "run-hooks",
            "help": 'Run hooks provided comma separated ("prebuild,postbuild")',
            "action": "store_list",
            "seperate_by": ",",
        },
    ]
    parsed_args = Namespace()
    if "help" in args or args == []:
        toprint = ""
        usage = "usage: boulder"
        for arg in arguments[1:]:
            toprint += f"\n  {arg['arg']}{(12 - len(arg['arg'])) * " "}{arg['help']}"
            if arg["action"] != "store_true":
                usage += f" [{arg['arg']} ...]"
            usage += f" [{arg['arg']}]"
        print(usage)
        print()
        print(arguments[0])
        print(f"\nArguments:")
        print(f"{toprint[1:]}\n  help{" " * 8}Show this message")
        exit(0)
    else:
        for arg in arguments[1:]:
            if arg["arg"] in args:
                if arg["action"] == "store_true":
                    setattr(parsed_args, arg["arg"], True)
                elif arg["action"] == "store_list":
                    setattr(
                        parsed_args,
                        arg["arg"],
                        args[args.index(arg["arg"]) + 1].split(arg["seperate_by"]),
                    )
                else:
                    setattr(parsed_args, arg["arg"], args[args.index(arg["arg"]) + 1])
            else:
                if arg["action"] == "store_true":
                    setattr(parsed_args, arg["arg"], False)
                else:
                    setattr(parsed_args, arg["arg"], None)
        return parsed_args
