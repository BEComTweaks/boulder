import os, re, inspect, traceback, subprocess
from pathlib import Path
from sys import executable as pyexe
from typing import Union

global project_path
projectPath = os.getcwd()


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


class Console:
    def __init__(self, verbose: bool = False, allow_tips: bool = True):
        self.verbose = verbose
        self.tips = allow_tips

    def _format(self, tag, color, message):
        tag = tag.ljust(6)  # Centers the text inside the tag
        print(f"{Fore.BLACK}{color} {tag} {Fore.RESET}{Back.RESET} {message}")

    def log(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            color = Back.LIGHTCYAN_EX if (vb and self.verbose) else Back.CYAN
            self._format("INFO", color, message)

    def error(
        self,
        message,
        doexit: bool = False,
        vb: bool = False,
        show_traceback: bool = True,
    ):
        if (vb and self.verbose) or not vb:
            filename, _ = get_caller_info()
            tb = traceback.format_exc()
            if "NoneType" not in tb and self.verbose and show_traceback:
                lines = message.split("\n") + tb.split("\n")[-5:-1]
            else:
                lines = message.split("\n")
            move_by = len(f"{filename}: ")
            color = Back.LIGHTRED_EX if (vb and self.verbose) else Back.RED
            self._format("ERROR", color, f"{filename}: {lines[0]}")
            for line in lines[1:]:
                if line != "":
                    self._format("ERROR", color, f"{move_by * " "}{line}")
        if doexit and not (vb and self.verbose):
            exit(1)

    def warn(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            filename, _ = get_caller_info()
            color = Back.LIGHTYELLOW_EX if (vb and self.verbose) else Back.YELLOW
            self._format("WARN", color, f"{filename}: {message}")

    def watch(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            color = Back.BLUE if (vb and self.verbose) else Back.LIGHTBLUE_EX
            self._format("WATCH", color, message)

    def dev(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            self._format("DEV", Back.LIGHTBLACK_EX, message)  # black wont work

    def config(self, message, vb: bool = False):
        if (vb and self.verbose) or not vb:
            color = Back.LIGHTMAGENTA_EX if (vb and self.verbose) else Back.MAGENTA
            self._format("CONFIG", color, message)

    def tip(self, message):
        if self.tips:
            self._format("TIP", Back.GREEN, message)

    def input(self, message):
        return input(
            f"{Fore.BLACK}{Back.LIGHTWHITE_EX} INPUT  {Fore.RESET}{Back.RESET} {message} "
        )


console = Console()


def run(command: Union[str, list], console_instance=console):
    try:
        if console_instance.verbose:
            print(
                f"{Fore.BLACK}{Back.LIGHTWHITE_EX} RUN    {Fore.RESET}{Back.RESET} {command if isinstance(command, str) else ' '.join(command)}"
            )
        output = subprocess.run(
            command, capture_output=True, text=True, shell=True, timeout=90
        )
        if "error" in output.stdout:
            output.returncode = 1
            output.stderr = output.stdout
        return output
    except subprocess.TimeoutExpired:
        console.error("Command timed out after 90 seconds.", doexit=True)
    except KeyboardInterrupt:
        console.error("Keyboard Interrupt", doexit=True)


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


def update_project_path():
    global projectPath
    projectPath = os.getcwd()


def project_path():
    return projectPath


def load_boulder_config():
    current_path = Path(project_path())
    while current_path != current_path.parent:
        config_path = current_path / "boulder_config.json"
        if config_path.exists():
            return load_json(config_path)
        current_path = current_path.parent


def boulder_path():
    return Path(__file__).parent


def load_global_config():
    global_location = boulder_path() / "config.json"
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


class RepoIssue(Exception):
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


def set_env_var(name, value):
    os.environ[name] = value
