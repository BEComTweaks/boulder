import os, re
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
            self._format("ERROR", Back.RED, message)
            if doexit and not (vb and self.verbose):
                exit(1)

    def warn(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("WARN", Back.YELLOW, message)

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

class Git:
    def __init__(self, repo_url: str, local_path: str):
        self.repo_url = repo_url
        self.local_path = local_path
        if os.path.exists(self.local_path):
            self.branch = check_branch(run(["git", "-C", self.local_path, "branch"], capture_output=True, text=True))
            
                

    def clone(self):
        if not os.path.exists(self.local_path):
            result = run(
                ["git", "clone", self.repo_url, self.local_path, "--depth=1"],
                capture_output=True,
                text=True,
            )
            if result.stderr == "":
                self.branch = check_branch(run(["git", "-C", self.local_path, "branch"], capture_output=True, text=True))
                return Namespace(success=True, output=result.stdout)
            else:
                return Namespace(success=False, output=result.stderr)
        else:
            return Namespace(success=False, output=None)

    def pull(self):
        if os.path.exists(self.local_path):
            os.chdir(self.local_path)
            # I love black's formatting
            result = run(
                [
                    "git",
                    "fetch",
                    "--depth=1",
                    "&&",
                    "git",
                    "reset",
                    "--hard",
                    "origin/main",
                    "&&",
                    "git",
                    "reflog",
                    "expire",
                    "--all",
                    "--expire=now",
                    "&&",
                    "git",
                    "gc",
                    "--prune=now",
                ],
                capture_output=True,
                text=True,
            )
            if result.stderr == "":
                return Namespace(success=True, output=result.stdout)
            else:
                return Namespace(success=False, output=result.stderr)
        else:
            return Namespace(success=False, output=None)

    def checkout(self, type:str, to_what: str):
        if os.path.exists(self.local_path):
            if type == "tag":
                to_what = f"tags/{to_what}"
            result = run(
                ["git", "-C", self.local_path, "checkout", to_what],
                capture_output=True,
                text=True,
            )    
            if result.stderr == "":
                self.branch = check_branch(run(["git", "-C", self.local_path, "branch"], capture_output=True, text=True))
                return Namespace(success=True, output=result.stdout)
            else:
                return Namespace(success=False, output=result.stderr)
        else:
            return Namespace(success=False, output=None)


def parser(args):
    arguments = [
        f"Boulder: {Fore.GREEN}Regolith, built with Python{Fore.RESET}",
        {
            "arg": "build",
            "help": f"Builds the project to your other folder.",
            "action": "store_true",
            "conflict": ["run-hooks", "add-hooks"],
        },
        {
            "arg": "dev",
            "help": "Builds and moves the project automatically to the development folder",
            "action": "store_true",
            "enable": ["build"],
            "conflict": ["run-hooks", "add-hooks"],
        },
        {
            "arg": "init",
            "help": "Initialize a Boulder project",
            "action": "store_true",
            "conflict": ["run-hooks", "add-hooks"],
        },
        {
            "arg": "watch",
            "help": "Watches the project for changes and builds it automatically",
            "action": "store_true",
            "enable": ["build"],
            "conflict": ["run-hooks", "add-hooks"],
        },
        {"arg": "verbose", "help": "Enable verbose output", "action": "store_true"},
        {
            "arg": "run-hooks",
            "help": f'Run hooks provided comma separated ({Fore.CYAN}"prebuild,postbuild"{Fore.RESET})',
            "action": "store_list",
            "separate_by": ",",
            "conflict": ["build", "dev", "watch", "init", "add-hooks"],
        },
        {
            "arg": "add-hooks",
            "help": "Add hooks to the project",
            "action": "store_true",
            "conflict": ["run-hooks", "build", "dev", "watch", "init"],
        },
    ]
    parsed_args = Namespace()
    enabled_args = set()

    if "help" in args or args == []:
        toprint = ""
        usage = "usage: boulder"
        for arg in arguments[1:]:
            toprint += f"\n  {arg['arg']}{(12 - len(arg['arg'])) * ' '}{arg['help']}"
            if arg["action"] != "store_true":
                usage += f" [{arg['arg']} ...]"
            usage += f" [{arg['arg']}]"
        print(
            f"{usage}\n\n{arguments[0]}\n\nArguments:\n{toprint[1:]}\n  help{' ' * 8}Show this message"
        )
        exit(0)
    else:
        for arg in arguments[1:]:
            if arg["arg"] in args:
                if arg["action"] == "store_true":
                    setattr(parsed_args, arg["arg"], True)
                    enabled_args.add(arg["arg"])
                elif arg["action"] == "store_list":
                    setattr(
                        parsed_args,
                        arg["arg"],
                        args[args.index(arg["arg"]) + 1].split(arg["separate_by"]),
                    )
                    enabled_args.add(arg["arg"])
                else:
                    setattr(parsed_args, arg["arg"], args[args.index(arg["arg"]) + 1])
                    enabled_args.add(arg["arg"])
            else:
                if arg["action"] == "store_true":
                    setattr(parsed_args, arg["arg"], False)
                else:
                    setattr(parsed_args, arg["arg"], None)
        # Enable if enabled
        for arg in arguments[1:]:
            if arg["arg"] in enabled_args and "enable" in arg:
                for enable_arg in arg["enable"]:
                    setattr(parsed_args, enable_arg, True)
                    enabled_args.add(enable_arg)
        # Check if conflict
        for arg in arguments[1:]:
            if arg["arg"] in enabled_args and "conflict" in arg:
                for conflict_arg in arg["conflict"]:
                    if conflict_arg in enabled_args:
                        console.error(
                            f"Argument '{Fore.GREEN}{arg['arg']}{Fore.RESET}' conflicts with '{Fore.RED}{conflict_arg}{Fore.RESET}'",
                            doexit=True,
                        )

        return parsed_args
