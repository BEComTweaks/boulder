from custom_functions import *
from shutil import copytree, rmtree
from subprocess import run
from maps import *

try:
    from os import makedirs, chdir

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
    console.log(args, vb=True)
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
    else:
        if args.build:
            project_loc = project_path()
            main_loc = boulder_path()
            console.log("Building started")
            try:
                makedirs(f"{main_loc}/build/{boulder_config['manifest']['name']}")
            except FileExistsError:
                console.warn("Build directory already exists", vb=True)
            rmtree(f"{main_loc}/build/{boulder_config['manifest']['name']}")
            copytree(f"{project_loc}/src", f"{main_loc}/build/{boulder_config['manifest']['name']}")
            chdir(f"{main_loc}/build/{boulder_config['manifest']['name']}")
            console.log("Copied files to seperate directory", vb=True)
            console.log("Loading hooks")
            try:
                makedirs(f"{main_loc}/hooks")
            except FileExistsError:
                pass
            try:
                for remote_hook in boulder_config["hooks"]["remote"]:
                    repo = Git(f"{main_loc}/hooks", remote_hook["repo"])
                    output = repo.clone()
                    if output.output == None:
                        # Repo already exists
                        repo.pull()
                        if not output.success:
                            console.error("Could not clone hooks!")
                            raise BuildIssue(output.output)
                    elif not output.success:
                        console.error("Could not clone hooks!")
                        raise BuildIssue(output.output)
                    else:
                        try:
                            if remote_hook["checkout_type"] == "branch" and remote_hook["checkout"] != repo.branch:
                                repo.checkout("branch", remote_hook["checkout"])
                        except KeyError:
                            pass
                        
                    try:
                        if remote_hook["regolith"]:
                            # Regolith has a different format
                            filter_def = load_json(f"{repo.local_path}/{remote_hook["name"]}/filter.json")
                            run([filter_def["filters"][0]["runWith"], f"{repo.local_path}/{remote_hook["name"]}/{filter_def["filters"][0]["script"]}"])
                        else:
                            raise KeyError # why is regolith false, what are you doing
                    except KeyError:
                        boulder_hooks = load_json(f"{repo.local_path}/.boulder_hooks.json")
                        for hook in boulder_hooks:
                            if hook["name"] == remote_hook["name"]:
                                for commands in hook["run"]:
                                    run(shell_caller(f"{repo.local_path}/{commands}"))
                for local_hook in boulder_config["hooks"]["local"]:
                    run(shell_caller(f"{project_loc}/{local_hook["file"]}"))
            except KeyError:
                console.error("Hook format is invalid!")
                console.tip("Try making a hook with boulder instead of manually!")
                exit(1)
            except BuildIssue as e:
                console.error(e, doexit=True)
except KeyboardInterrupt:
    console.error("KeyboardInterrupt", doexit=True)