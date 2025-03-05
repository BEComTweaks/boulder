from subprocess import run
from sys import executable as pyexe
import os

if str(os.getcwd()).endswith("system32"):
    # This has to be in every script to prevent FileNotFoundError
    # Because for some reason, it runs it at C:\Windows\System32
    # Yeah, it is stupid, but I can't put these lines in custom_functons
    # Because that still brings up an error
    os.chdir(os.path.dirname(os.path.realpath(__file__)))


# Get necessary files
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

require("requests")
import requests
import os, json

# Different terminal types need different installations
if os.name == "nt":
    if "HOME" in os.environ and "USERPROFILE" in os.environ:
        terminal_type = "unix"
    else:
        terminal_type = "cmd"
        import winreg
else:
    terminal_type = "unix"


# More random functions
def print_tag(tag, message):
    if tag == "error":
        print(f"{Fore.BLACK}{Back.RED} ERROR {Fore.RESET}{Back.RESET}\t {message}")
    elif tag == "watch":
        print(f"{Fore.BLACK}{Back.BLUE} WATCH {Fore.RESET}{Back.RESET}\t {message}")
    elif tag == "dev":
        print(
            f"{Fore.BLACK}{Back.LIGHTBLACK_EX} DEV {Fore.RESET}{Back.RESET}\t {message}"
        )
    elif tag == "warn":
        print(f"{Fore.BLACK}{Back.YELLOW} WARN {Fore.RESET}{Back.RESET}\t {message}")
    elif tag == "info":
        print(f"{Fore.BLACK}{Back.CYAN} INFO {Fore.RESET}{Back.RESET}\t {message}")
    elif tag == "config":
        print(f"{Fore.BLACK}{Back.MAGENTA} CONFIG {Fore.RESET}{Back.RESET} {message}")


def load_config():
    with open("config.json", "r") as file:
        return json.loads(file.read())


def save_config(data):
    with open("config.json", "w") as file:
        file.write(json.dumps(data, indent=4))


# change branch name
remote_url = "https://raw.githubusercontent.com/BEComTweaks/boulder/refs/heads/im-cooking-please-wait/"
try:
    response = requests.get(f"{remote_url}/pull_to_local/files.json")
    if response.status_code == 200:
        print_tag("info", "Fetched files to install.")
        files = response.json()
        # Pull and save files
        for script in files["python"]:
            response = requests.get(f"{remote_url}/{script}")
            if response.status_code == 200:
                with open(script.split("/")[-1], "w") as file:
                    file.write(response.text)
            else:
                raise requests.exceptions.ConnectionError
        for other_file in files["others"]:
            response = requests.get(f"{remote_url}/{other_file}")
            if response.status_code == 200:
                with open(other_file.split("/")[-1], "w") as file:
                    file.write(response.text)
            else:
                raise requests.exceptions.ConnectionError
        print_tag("info", "Pulled all files")
        # Install to PATH
        new_path = os.path.dirname(__file__)
        if terminal_type == "cmd":
            # Windows while using pwsh/cmd
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
            ) as key:
                current_path = winreg.QueryValueEx(key, "Path")[0]
                updated_path = current_path + ";" + new_path
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated_path)
            # Make 'exe'
            with open("boulder.bat", "w") as script:
                script.write('@echo off\npython "%~dp0main.py" %*')
            print_tag("info", "Added boulder to PATH")
            # Config path
            valid = False
            config = load_config()
            default_loc = os.path.join(
                os.environ["USERPROFILE"],
                "AppData",
                "Local",
                "Packages",
                "Microsoft.MinecraftUWP_8wekyb3d8bbwe",
                "LocalState",
                "games",
                "com.mojang",
            )
            while not valid:
                print_tag(
                    "config",
                    "Is your Minecraft installation located at the default location? (y/n)",
                )
                print_tag("config", f"Default Location: {default_loc}")
                answer = input().lower()
                if answer == "y":
                    config["minecraft_path"] = str(default_loc)
                    valid = True
                elif answer == "n":
                    print_tag(
                        "config", "Where is your Minecraft installation located at?"
                    )
                    new_loc = input()
                    if os.path.exists(new_loc):
                        if "minecraftpe" in os.listdir(new_loc):
                            config["minecraft_path"] = new_loc
                            valid = True
                        else:
                            print_tag(
                                "error", "The path entered isn't the right folder"
                            )
                    else:
                        print_tag("error", "Invalid path to installation")
        else:
            # Unix/WSL
            valid = False
            while not valid:
                print_tag("config", "I need more info on your terminal installation!")
                print_tag(
                    "config",
                    "Please input the terminal's type (`bash`, `zsh`, `fish`, etc)",
                )
                terminal_type = input()
                shell_rc = os.path.join(os.environ["HOME"], f".{terminal_type}rc")
                if os.path.exists(shell_rc):
                    with open(shell_rc, "a") as file:
                        file.write(f"export PATH=$PATH:{new_path}\n")
                    valid = True
                else:
                    print_tag("error", "Give the Terminal's actual name")
            # Add to PATH + make 'exe'
            with open("boulder", "w") as script:
                script.write('#!/bin/bash\npython "$(dirname "$0")/main.py" "$@"')
            os.system("chmod +x boulder")
            print_tag("info", "Added boulder to PATH")
            # Config path
            valid = False
            while not valid:
                print_tag(
                    "config",
                    "I am not sure where your Minecraft installation is located at.",
                )
                print_tag(
                    "config",
                    "Please input the path to your Minecraft installation's `com.mojang` folder.",
                )
                loc = input()
                if os.path.exists(loc):
                    valid = True
                    if "minecraftpe" in os.listdir(loc):
                        config = load_config()
                        config["minecraft_path"] = loc
                        valid = True
                else:
                    print_tag("error", "Invalid path")
        allow_tips = ""
        while allow_tips.lower() not in ["y", "n"]:
            print_tag("config", "Do you want tips and tricks? (Y/n)")
            allow_tips = input()
        config["show_tips"] = allow_tips == "y"
        save_config(config)
        os.remove(__file__)
        print_tag("info", "Install successful!")
    else:
        raise requests.exceptions.ConnectionError
except requests.exceptions.ConnectionError:
    print_tag("error", "Failed to fetch files to install.")
    try:
        print_tag("error", f"Status code: {response.status_code}")
    except NameError:
        print_tag("error", "Please connect to an active internet connection.")
    exit(1)
