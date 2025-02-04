from custom_functions import *

console = Console()

from os import makedirs, chdir, remove
from shutil import copytree, rmtree, which

require("watchdog")
from watchdog.events import FileSystemEventHandler

try:
    makedirs(f"{boulder_path()}/hooks")
except FileExistsError:
    pass


class Git:
    def __init__(self, repo_url: str, local_path: str):
        self.repo_url = repo_url
        self.local_path = local_path
        if os.path.exists(self.local_path):
            self.branch = check_branch(run(["git", "-C", self.local_path, "branch"]))

    def clone(self):
        if not os.path.exists(self.local_path):
            result = run(["git", "clone", self.repo_url, self.local_path])
            if result.returncode == 0:
                self.branch = check_branch(
                    run(["git", "-C", self.local_path, "branch"])
                )
                return Namespace(
                    success=True, output=f"{result.stdout}\n{result.stderr}"
                )
            else:
                return Namespace(
                    success=False, output=f"{result.stdout}\n{result.stderr}"
                )
        else:
            return Namespace(success=False, output=None)

    def pull(self):
        if os.path.exists(self.local_path):
            os.chdir(self.local_path)
            # I love black's formatting
            result = run(["git", "pull", "--rebase"])
            if result.returncode == 0:
                return Namespace(
                    success=True, output=f"{result.stdout}\n{result.stderr}"
                )
            else:
                return Namespace(
                    success=False, output=f"{result.stdout}\n{result.stderr}"
                )
        else:
            return Namespace(success=False, output=None)

    def checkout(self, type: str, to_what: str):
        if os.path.exists(self.local_path):
            if type == "tag":
                to_what = f"tags/{to_what}"
            result = run(["git", "-C", self.local_path, "checkout", to_what])
            if result.returncode == 0:
                self.branch = check_branch(
                    run(
                        ["git", "-C", self.local_path, "branch"],
                        capture_output=True,
                        text=True,
                    )
                )
                return Namespace(success=True, output=result.stdout)
            else:
                return Namespace(success=False, output=result.stderr)
        else:
            return Namespace(success=False, output=None)


def parser(args):
    arguments = [
        f"Boulder: {Fore.GREEN}Regolith, built with Python{Fore.RESET}",
        {
            "arg": "init",
            "help": "Initialize a Boulder project",
            "action": "store_true",
            "conflict": ["hooks"],
            "color": "BLUE",
        },
        {
            "arg": "build",
            "help": f"Builds the project to your other folder.",
            "action": "store_true",
            "conflict": ["hooks"],
            "color": "GREEN",
        },
        {
            "arg": "dev",
            "help": "Builds and moves the project automatically to the development folder",
            "action": "store_true",
            "enable": ["build"],
            "conflict": ["hooks"],
            "color": "GREEN",
        },
        {
            "arg": "watch",
            "help": "Watches the project for changes and builds it automatically",
            "action": "store_true",
            "enable": ["build"],
            "conflict": ["hooks"],
            "color": "GREEN",
        },
        {
            "arg": "hooks",
            "help": f'Add, list or run hooks. Use "{Fore.GREEN}boulder hooks help{Fore.RESET}" for more information',
            "action": "store_all",
            "separate_by": ",",
            "conflict": ["build", "dev", "watch", "init"],
            "format": [
                ["add", "<repo>", "<name>", "<checkout_type>", "<checkout>"],
                ["list"],
                ["run", "<name>"],
            ],
            "color": "CYAN",
        },
        "new-line",
        {"arg": "verbose", "help": "Enable verbose output", "action": "store_true"},
        {
            "arg": "cd",
            "help": "Use a different directory instead of the current one",
            "action": "store_str",
        },
        {"arg": "help", "help": "Show this message", "action": "store_true"},
    ]
    parsed_args = Namespace()
    if args[0] == "help" or args == []:
        toprint = ""
        usage = "usage: boulder"
        for arg in arguments[1:]:
            if arg == "new-line":
                toprint += "\n"
                continue
            try:
                toprint += f"\n  {Fore.__dict__[arg['color']]}{arg['arg']}{Fore.RESET}{(12 - len(arg['arg'])) * ' '}{arg['help']}"
            except KeyError:
                toprint += (
                    f"\n  {arg['arg']}{(12 - len(arg['arg'])) * ' '}{arg['help']}"
                )
            if arg["action"] != "store_true":
                usage += f" [{arg['arg']} ...]"
            else:
                usage += f" [{arg['arg']}]"
        print(f"{usage}\n\n{arguments[0]}\n\nArguments:\n{toprint[1:]}")
        print(
            f"\n  Colors:\n  WHITE{7 * ' '}Can be used with any command\n  Others{6 * ' '}Can only be used with other commands of the same color"
        )
        exit(0)
    else:
        mapped_args = {
            "arg": [],
            "action": [],
            "format": [],
            "conflict": [],
            "enable": [],
        }
        for arg in arguments:
            if type(arg) == str:
                continue
            else:
                mapped_args["arg"].append(arg["arg"])
                mapped_args["action"].append(arg["action"])
                if arg["action"] == "store_true":
                    setattr(parsed_args, arg["arg"], False)
                else:
                    setattr(parsed_args, arg["arg"], None)
                mapped_args["format"].append(arg["format"] if "format" in arg else None)
                mapped_args["conflict"].append(
                    arg["conflict"] if "conflict" in arg else None
                )
                mapped_args["enable"].append(arg["enable"] if "enable" in arg else None)
        next_arg_is_saved = False
        next_args_are_saved = False
        save_args_to = None
        enabled_args = []
        # Set the values for the added arguments
        for arg in args:
            if next_arg_is_saved:
                next_arg_is_saved = False
                continue
            elif next_args_are_saved:
                setattr(
                    parsed_args,
                    save_args_to,
                    getattr(parsed_args, save_args_to, []) + [arg],
                )
            elif arg not in mapped_args["arg"]:
                console.error(
                    f"Unknown argument '{Fore.RED}{arg}{Fore.RESET}'", doexit=True
                )
            else:
                arg_index = mapped_args["arg"].index(arg)
                if mapped_args["conflict"][arg_index] != None:
                    for i in mapped_args["conflict"][arg_index]:
                        if i in enabled_args:
                            console.error(
                                f"Argument '{Fore.RED}{arg}{Fore.RESET}' conflicts with '{Fore.RED}{i}{Fore.RESET}'",
                                doexit=True,
                            )
                enabled_args.append(arg)
                if mapped_args["action"][arg_index] == "store_true":
                    setattr(parsed_args, arg, True)
                    enabled_args.append(arg)
                elif mapped_args["action"][arg_index] == "store_str":
                    setattr(parsed_args, arg, args[args.index(arg) + 1])
                    next_arg_is_saved = True
                    enabled_args.append(arg)
                elif mapped_args["action"][arg_index] == "store_all":
                    save_args_to = arg
                    setattr(parsed_args, arg, [])
                    next_args_are_saved = True
                if mapped_args["enable"][arg_index] != None:
                    for enable_arg in mapped_args["enable"][arg_index]:
                        setattr(parsed_args, enable_arg, True)
                        enabled_args.append(enable_arg)
        return parsed_args


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, exclude_files):
        self.exclude_files = exclude_files

    def on_any_event(self, event):
        if (
            any(event.src_path.endswith(exclude) for exclude in self.exclude_files)
            or event.is_directory
        ):
            return
        console.watch(f"Change detected in {event.src_path}")
        build()


def setVars(config_global, config_boulder):
    global global_config
    global boulder_config
    global_config = config_global
    boulder_config = config_boulder


def init():
    template_config = load_from_remote(
        "pull_to_local/template_config.json", isJson=True
    )
    try:
        makedirs("src/rp")
        makedirs("src/bp")
    except FileExistsError:
        console.warn("Cannot initialise directories, they already exist!", vb=True)
    console.config("Let's get started!")
    template_config["manifest"]["name"] = console.input("What is your project's name?")
    template_config["manifest"]["description"] = console.input(
        "What is a description for the project?"
    )
    version = ""
    while len(version.split(".")) != 3:
        version = console.input('The version for the project? (e.g. "1.2.5")')
    template_config["manifest"]["version"] = version
    console.log("All done, have fun!")
    dump_json("boulder_config.json", template_config)
    if global_config["show_tips"]:
        console.tip("Hooks can be set up to make your experience a lot better!")


def build():
    project_loc = project_path()
    main_loc = boulder_path()
    console.log("Building started")
    try:
        makedirs(f"{main_loc}/build/{boulder_config['manifest']['name']}")
    except FileExistsError:
        console.warn("Build directory already exists", vb=True)
        try:
            rmtree(f"{main_loc}/build/{boulder_config['manifest']['name']}")
        except PermissionError:
            console.error(
                "Build directory is being used by another process, please close it and try again!"
            )
    copytree(
        f"{project_loc}/src", f"{main_loc}/build/{boulder_config['manifest']['name']}"
    )
    chdir(f"{main_loc}/build/{boulder_config['manifest']['name']}")
    console.log("Copied files to seperate directory", vb=True)
    console.log("Loading repositories of hooks")
    project_build_loc = f"{main_loc}/build/{boulder_config['manifest']['name']}"
    try:
        makedirs(f"{main_loc}/hooks")
    except FileExistsError:
        pass
    try:
        for remote_hook in boulder_config["hooks"]["remote"]:
            repo = Git(
                remote_hook["repo"],
                f"{main_loc}/hooks/{remote_hook['repo'].split('/')[-1]}",
            )
            output = repo.clone()
            if output.output == None:
                # Repo already exists
                output = repo.pull()
                if not output.success:
                    console.error("Could not clone hooks!")
                    raise BuildIssue(output)
            elif not output.success:
                console.error("Could not clone hooks!")
                raise BuildIssue(output.output)
            else:
                try:
                    if (
                        remote_hook["checkout_type"] == "branch"
                        and remote_hook["checkout"] != repo.branch
                    ):
                        repo.checkout("branch", remote_hook["checkout"])
                except KeyError:
                    pass
            os.chdir(f"{project_build_loc}")
            console.log(f"Running hook `{remote_hook['name']}`")
            try:
                if remote_hook["regolith"]:
                    # Regolith has a different format
                    filter_def = load_json(
                        f"{repo.local_path}/{remote_hook["name"]}/filter.json"
                    )
                    run(
                        [
                            filter_def["filters"][0]["runWith"],
                            f"{repo.local_path}/{remote_hook["name"]}/{filter_def["filters"][0]["script"]}",
                        ]
                    )
                else:
                    raise KeyError  # why is regolith false, what are you doing
            except KeyError:
                boulder_hooks = load_json(f"{repo.local_path}/.boulder_hooks.json")
                for hook in boulder_hooks:
                    if hook["name"] == remote_hook["name"]:
                        for command in hook["run"]:
                            if command.startswith("cd:"):
                                chdir(f"{project_build_loc}/{command.split(': ')[1]}")
                            elif "." in command.split(os.path.sep)[-1]:
                                run([f"{repo.local_path}/{command}"])
                            else:
                                command = command.split(" ")
                                command[0] = which(command[0])
                                run(command)
                        try:
                            console.log("Cleaning up hook's trash...")
                            chdir(f"{project_build_loc}")
                            for files in hook["cleanup"]:
                                try:
                                    if files.endswith("/"):
                                        rmtree(f"{project_build_loc}/{files}")
                                    else:
                                        remove(f"{project_build_loc}/{files}")
                                except FileNotFoundError:
                                    console.warn(f"Could not find {files} to remove")
                        except KeyError:
                            pass
        for local_hook in boulder_config["hooks"]["local"]:
            run([f"{project_build_loc}/{local_hook["file"]}"])
            try:
                for files in hook["cleanup"]:
                    console.log("Cleaning up hook's trash...")
                    if files.endswith("/"):
                        rmtree(f"{repo.local_path}/{files}")
                    else:
                        remove(f"{repo.local_path}/{files}")
            except KeyError:
                pass
        console.log("Generating manifest...")

    except KeyError:
        console.error("Hook format is invalid!")
        console.tip("Try making a hook with boulder instead of manually!")
        exit(1)
    except BuildIssue as e:
        console.error(e, doexit=True)
