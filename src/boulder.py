from custom_functions import *

console = Console()

require("colorama")
from colorama import *
import argparse

args = argparse.ArgumentParser(
    description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}",
    add_help=False
)
args.add_argument("args", nargs="*")
args = parser(args.parse_args().args)

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
