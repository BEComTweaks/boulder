from custom_functions import *

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
    args = parser(args.parse_args().args)
    console = Console(args.verbose)
    global_config = load_global_config()
    console.tips = global_config["show_tips"]
    console.log("Loaded global config", vb=True)
    console.log("Loaded arguments", vb=True)
    boulder_config = load_boulder_config()
    if boulder_config == None:
        console.warn("Project config not found", vb=True)
    else:
        console.log("Loaded project config", vb=True)
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
            console.warn("Cannot initialise directories, they already exist!", vb=True)
        console.config("Let's get started!")
        template_config["manifest"]["name"] = console.input("What is your project's name?")
        template_config["manifest"]["description"] = console.input("What is a description for the project?")
        version = ""
        while len(version.split(".")) != 3:
            version = console.input("The version for the project? (e.g. \"1.2.5\")")
        template_config["manifest"]["version"] = version
        console.log("All done, have fun!")
        dump_json("boulder_config.json", template_config)
        if global_config["show_tips"]:
            console.tip("Hooks can be set up to make your experience a lot better!")
    else: pass
except KeyboardInterrupt:
    console.error("KeyboardInterrupt", doexit=True)