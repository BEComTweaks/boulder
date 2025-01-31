from custom_functions import *

console = Console()

require("colorama")
from colorama import *
import argparse

args = argparse.ArgumentParser(
    description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}"
)
args.add_argument(
    "-b",
    "--build",
    help=f"Builds the project to your other folder.{Fore.RED}This is automatically enabled when running --watch and/or --dev",
)
args.add_argument(
    "-d",
    "--dev",
    help="Builds and moves the project automatically to the development folder",
    action="store_true",
)
args.add_argument(
    "-w",
    "--watch",
    help="Watches the project for changes and builds it automatically",
    action="store_true",
)
args.add_argument("-v", "--verbose", help="Enable verbose mode", action="store_true")
args.add_argument(
    "-i", "--init", help="Initialize a Boulder project", action="store_true"
)
args = args.parse_args()

boulder_config = load_boulder_config()
if boulder_config == None and not args.init:
    console.error("Could not find boulder_config.json")
    console.tip("Did you mean to initialize?")
    exit(1)
elif boulder_config != None and args.init:
    console.error("Boulder is already initialized!", doexit=True)
elif boulder_config == None and args.init:
    pass
else:
    console.log(boulder_config)
