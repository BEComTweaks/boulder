from custom_functions import *

try:
    from os import chdir
    from time import sleep
    import core, argparse
    import hook_handler as hh

    require("colorama")
    from colorama import *

    require("watchdog")
    from watchdog.observers import Observer

    args = argparse.ArgumentParser(
        description=f"Boulder\n{Fore.CYAN}Regolith, built with Python{Fore.RESET}",
        add_help=False,
    )
    args.add_argument("args", nargs="*")
    args = core.parser(args.parse_args().args)
    console = Console(args.verbose)
    if args.cd:
        chdir(args.cd)
        update_project_path()
    global_config = load_global_config()
    console.tips = global_config["show_tips"]
    console.log("Loaded global config", vb=True)
    console.log("Loaded arguments", vb=True)
    console.log(args, vb=True)
    boulder_config = load_boulder_config()
    core.setCoreVars(global_config, boulder_config, console)
    hh.setHookHandlerVars(global_config, boulder_config, console)
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
            core.build()
            console.watch("Waiting for changes...")
            try:
                event_handler = core.ChangeHandler(
                    boulder_config["watchdog_exclude"]
                    + [boulder_config["folders"]["behaviour_pack"]]
                )
            except KeyError:
                event_handler = core.ChangeHandler(
                    [boulder_config["folders"]["behaviour_pack"]]
                )
            observer = Observer()
            observer.schedule(event_handler, ".", recursive=True)
            observer.start()
            while True:
                sleep(1)  # There is literally no other way to do this
        elif args.build:
            core.build(args.dev)
        elif args.hooks:
            # handle hooks
            arg = args.hooks
            if arg[0] == "help":
                hh.help()
            elif arg[0] == "add":
                hh.add_hook(arg[1:])
            elif arg[0] == "remove":
                hh.remove_hook(arg[1:])
            elif arg[0] == "list":
                hh.list_hooks()
            elif arg[1] in ["switch", "checkout"]:
                hh.checkout(arg)
            else:
                console.error("Invalid argument, try 'boulder hooks help'")
except KeyboardInterrupt:
    console.error("KeyboardInterrupt", doexit=True)
    try:
        observer.stop()
        observer.join()
    except NameError:
        pass
