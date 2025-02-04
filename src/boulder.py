from custom_functions import *

try:
    from os import chdir
    import core, argparse

    require("colorama")
    from colorama import *
    
    require("watchdog")
    from watchdog.observers import Observer

    args = argparse.ArgumentParser(
        description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}",
        add_help=False
    )
    args.add_argument("args", nargs="*")
    args = core.parser(args.parse_args().args)
    console = Console(args.verbose)
    if args.cd:
        chdir(args.cd)
    global_config = load_global_config()
    console.tips = global_config["show_tips"]
    console.log("Loaded global config", vb=True)
    console.log("Loaded arguments", vb=True)
    console.log(args, vb=True)
    boulder_config = load_boulder_config()
    core.setVars(global_config, boulder_config)
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
        core.init()
    else:
        if args.watch:
            event_handler = core.ChangeHandler(boulder_config["project"]["watchdog_exclude"])
            observer = Observer()
            observer.schedule(event_handler, ".", recursive=True)
            observer.start()
        elif args.build:
            core.build()
        elif args.add_hook:
            pass
except KeyboardInterrupt:
    console.error("KeyboardInterrupt", doexit=True)
    try:
        observer.stop()
        observer.join()
    except NameError:
        pass