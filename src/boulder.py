from custom_functions import *
console = Console()

require("colorama")
from colorama import *
import argparse

args = argparse.ArgumentParser(description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}")
args.add_argument("-d", "--dev", help="Builds and moves the project automatically to the development folder")
args.add_argument("-w", "--watch", help="Watches the project for changes and builds it automatically")
args.add_argument("-v", "--verbose", help="Enable verbose mode", action="store_true")
args = args.parse_args()

boulder_config = load_boulder_config()

