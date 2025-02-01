from custom_functions import *
console = Console()

try:
    from os import makedirs

    require("colorama")
    from colorama import *
    import argparse

    args = argparse.ArgumentParser(
        description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}",
        add_help=False
    )
    args.add_argument("args", nargs="*")
    console.log(args.parse_args().args)
    args = parser(args.parse_args().args)
    console.log(args)

    boulder_config = load_boulder_config()
    if boulder_config == None and not args.init:
        console.error("Could not find boulder_config.json")
        console.tip("Did you mean to initialize?")
        exit(1)
    elif boulder_config != None and args.init:
        console.error("Boulder is already initialized!", doexit=True)
    elif boulder_config == None and args.init:
        template_config = load_from_remote("pull_to_local/template_config.json", isJson=True)
        try:
            makedirs("src/rp")
            makedirs("src/bp")
        except FileExistsError:
            console.warn("Cannot initialise directories, they already exist!")
        console.config("Let's get started!")
        template_config["manifest"]["name"] = console.input("What is your project's name?")
    else:
        console.log(boulder_config)
except KeyboardInterrupt:
    console.error("KeyboardInterrupt", doexit=True)