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