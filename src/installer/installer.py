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
require("requests")
import requests

def print_tag(tag, message):
    if tag == "error":
        print(f"{Back.RED} ERROR {Back.RESET}\t{message}")
    elif tag == "watch":
        print(f"{Back.BLUE} WATCH {Back.RESET}\t{message}")
    elif tag == "dev":
        print(f"{Back.LIGHTBLACK_EX} DEV {Back.RESET}\t{message}")
    elif tag == "warn":
        print(f"{Back.YELLOW} WARN {Back.RESET}\t{message}")
    elif tag == "info":
        print(f"{Back.CYAN} INFO {Back.RESET}\t{message}")

# change branch name
remote_url = "https://raw.githubusercontent.com/BEComTweaks/boulder/refs/heads/im-cooking-please-wait/src/"
response = requests.get(f'{remote_url}/installer/files.json')
if response.status_code == 200:
    print_tag("info", "Fetched files to install.")
    files = response.json()
    
else:
    print_tag("error", "Failed to fetch files to install.")
    print_tag("error", f"Status code: {response.status_code}")
    exit(1)