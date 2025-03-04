from custom_functions import *

console = Console()

from os import makedirs, chdir, remove
from shutil import copytree, rmtree, which, move
from uuid import uuid4
from datetime import datetime

require("watchdog")
from watchdog.events import FileSystemEventHandler
from types import SimpleNamespace as Namespace

require("requests")

try:
    makedirs(f"{boulder_path()}/hooks")
except FileExistsError:
    pass


template_manifest = {
    "format_version": 2,
    "header": {
        "name": "",
        "description": "",
        "uuid": "",
        "version": [1, 0, 0],
        "min_engine_version": [1, 16, 0],
    },
    "modules": [{"type": "", "description": "", "uuid": "", "version": [1, 0, 0]}],
    "dependencies": [],
}


class Git:
    def __init__(self, repo_url: str, local_path: str):
        self.repo_url = repo_url
        self.local_path = local_path
        if os.path.exists(self.local_path):
            self.branch = check_branch(
                run(["git", "-C", self.local_path, "branch"], console)
            )

    def clone(self):
        if not os.path.exists(self.local_path):
            result = run(["git", "clone", self.repo_url, self.local_path], console)
            if result.returncode == 0:
                self.branch = check_branch(
                    run(["git", "-C", self.local_path, "branch"], console)
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
            result = run(["git", "pull", "--rebase"], console)
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
            elif type not in ["tag", "branch", "commit"]:
                console.warn(f"I highly doubt {type} is a valid checkout type...")
            result = run(["git", "-C", self.local_path, "checkout", to_what], console)
            if result.returncode == 0:
                self.branch = check_branch(
                    run(["git", "-C", self.local_path, "branch"], console)
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
    if args == [] or args[0] == "help":
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


def setCoreVars(config_global, config_boulder, console_instance):
    global global_config
    global boulder_config
    global console
    global_config = config_global
    boulder_config = config_boulder
    console = console_instance


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


def check_repo(remote_hook: dict):
    repo_id = "-".join(
        remote_hook["repo"].split("/")[-2:]
    )  # get as a <creator>-<repo> format
    repo = Git(
        remote_hook["repo"],
        f"{boulder_path()}/hooks/{repo_id}",
    )
    if os.path.exists(repo.local_path):
        try:
            hook_list = load_json(f"{boulder_path()}/hooks/hook_list.json")
            if (
                (
                    hook_list[remote_hook["repo"]]["last_updated_at"]
                    + (global_config["update_hooks_after"] * 60)
                    < int(datetime.now().timestamp())
                )
                or ("checkout_type" not in remote_hook or "checkout" not in remote_hook)
                or (
                    remote_hook["checkout"]
                    != hook_list[remote_hook["repo"]]["checkout"]["at"]
                )
            ):
                console.log(
                    f"{"/".join(remote_hook["repo"].split("/")[-2:])} was last updated {int((datetime.now().timestamp() - hook_list[remote_hook["repo"]]["last_updated_at"]) / 60)} mins ago",
                    vb=True,
                )
                console.log("Updating hook...", vb=True)
                output = repo.pull()
                if not output.success:
                    console.error("Could not update repo!")
                    raise BuildIssue(output.output)
                else:
                    try:
                        # Checkout chosen branch/tag/commit
                        if (
                            remote_hook["checkout"]
                            != hook_list[remote_hook["repo"]]["checkout"]["at"]
                        ):
                            if remote_hook["checkout_type"] in [
                                "branch",
                                "tag",
                                "commit",
                            ]:
                                output = repo.checkout(
                                    remote_hook["checkout_type"],
                                    remote_hook["checkout"],
                                )
                                if not output.success:
                                    console.error(
                                        f"Could not checkout to {remote_hook["checkout"]}!"
                                    )
                                    console.error(output.output, doexit=True, vb=True)
                                else:
                                    hook_list[remote_hook["repo"]]["checkout"] = {
                                        "type": remote_hook["checkout_type"],
                                        "at": remote_hook["checkout"],
                                    }
                    except KeyError:
                        console.warn(
                            "No checkout type found, assuming default branch is `main`"
                        )
                        output = repo.checkout("branch", "main")
                        if not output.success:
                            console.error(f"Could not checkout to main!")
                            console.error(output.output, doexit=True, vb=True)
                        else:
                            hook_list[remote_hook["repo"]]["checkout"] = {
                                "type": "branch",
                                "at": "main",
                            }
                    console.log("Hook updated!", vb=True)
                    hook_list[remote_hook["repo"]]["last_updated_at"] = int(
                        datetime.now().timestamp()
                    )
                    dump_json(f"{boulder_path()}/hooks/hook_list.json", hook_list)
        except FileNotFoundError:
            console.error("Please do not manually add repos to the directory!")
            console.warn("Assuming the repo was cloned today...")
            dump_json(
                f"{boulder_path()}/hooks/hook_list.json",
                {
                    remote_hook["repo"]: {
                        "last_updated_at": int(datetime.now().timestamp())
                    }
                },
            )
    else:
        output = repo.clone()
        if not output.success:
            console.error("Could not clone hooks!")
            raise BuildIssue(output.output)
        else:
            try:
                try:
                    hook_list = load_json(f"{boulder_path()}/hooks/hook_list.json")
                except FileNotFoundError:
                    hook_list = {}
                hook_list[remote_hook["repo"]]["last_updated_at"] = int(
                    datetime.now().timestamp()
                )
                if (
                    remote_hook["checkout_type"] == "branch"
                    and remote_hook["checkout"] != repo.branch
                ) or remote_hook["checkout_type"] in ["tag", "commit"]:
                    output = repo.checkout(
                        remote_hook["checkout_type"], remote_hook["checkout"]
                    )
                else:
                    console.error(
                        f"What are you checking out? It needs to be a branch, tag or commit, not {remote_hook['checkout_type']}!"
                    )
                if not output.success:
                    console.error(f"Could not checkout to {remote_hook["checkout"]}!")
                    console.error(output.output, doexit=True, vb=True)
                else:
                    hook_list[remote_hook["repo"]]["checkout"] = {
                        "type": remote_hook["checkout_type"],
                        "at": remote_hook["checkout"],
                    }
            except KeyError:
                hook_list[remote_hook["repo"]] = {
                    "last_updated_at": int(datetime.now().timestamp()),
                    "checkout": {"type": "branch", "at": repo.branch},
                }
                pass
            dump_json(f"{boulder_path()}/hooks/hook_list.json", hook_list)
    return repo


def build(dev_mode=False):
    project_loc = project_path()
    boulder_path = boulder_path()
    console.log("Building started")
    try:
        makedirs(f"{boulder_path}/build/{boulder_config['manifest']['name']}")
    except FileExistsError:
        console.warn("Build directory already exists", vb=True)
        rmtree(f"{boulder_path}/build/{boulder_config['manifest']['name']}")
    try:
        copytree(
            f"{project_loc}/{boulder_config["folders"]["source"]}",
            f"{boulder_path}/build/{boulder_config['manifest']['name']}",
        )
    except FileExistsError:
        console.warn("Safeguards were breached, attempting to fix", vb=True)
        rmtree(f"{boulder_path}/build/{boulder_config['manifest']['name']}")
        copytree(
            f"{project_loc}/{boulder_config["folders"]["source"]}",
            f"{boulder_path}/build/{boulder_config['manifest']['name']}",
        )
    chdir(f"{boulder_path}/build/{boulder_config['manifest']['name']}")
    console.log("Copied files to seperate directory", vb=True)
    console.log("Loading repositories of hooks")
    project_build_loc = f"{boulder_path}/build/{boulder_config['manifest']['name']}"
    try:
        makedirs(f"{boulder_path}/hooks")
    except FileExistsError:
        pass
    try:
        set_env_var("PROJECT_PATH", project_build_loc)
        try:
            set_env_var(
                "PROJECT_PATH_BP",
                f"{project_build_loc}/{boulder_config['folders']['behaviour_pack']}",
            )
        except KeyError:
            pass
        try:
            set_env_var(
                "PROJECT_PATH_RP",
                f"{project_build_loc}/{boulder_config['folders']['resource_pack']}",
            )
        except KeyError:
            pass
        for remote_hook in boulder_config["hooks"]["remote"]:
            repo = check_repo(remote_hook)
            os.chdir(f"{project_build_loc}")
            hook_exists = False
            boulder_hooks = load_json(f"{repo.local_path}/.boulder_hooks.json")
            for hook in boulder_hooks:
                if hook["id"] == remote_hook["id"]:
                    hook_exists = True
                    console.log(f"Running hook `{remote_hook["id"]}`")
                    for command in hook["run"]:
                        if command.startswith("cd:"):
                            chdir(f"{project_build_loc}/{command.split(': ')[1]}")
                        elif "." in command.split(os.path.sep)[-1]:
                            run([f"{repo.local_path}/{command}"], console)
                        else:
                            command = command.split(" ")
                            check = which(command[0])
                            if check != None:
                                command[0] = check
                            run(command, console)
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
            if not hook_exists:
                console.error(f"Hook with ID {remote_hook['id']} does not exist!")
                console.tip("Are you sure you are on the right branch?")
                exit(1)
        for local_hook in boulder_config["hooks"]["local"]:
            console.log(f"Running local hook `{local_hook['id']}`")
            for command in local_hook["run"]:
                if command.startswith("cd:"):
                    chdir(f"{project_build_loc}/{command.split(': ')[1]}")
                elif "." in command.split(os.path.sep)[-1]:
                    run([f"{project_build_loc}/{command}"], console)
                else:
                    command = command.split(" ")
                    check = which(command[0])
                    if check != None:
                        command[0] = check
                    run(command, console)
            try:
                console.log("Cleaning up hook's trash...")
                chdir(f"{project_build_loc}")
                for files in hook["cleanup"]:
                    if files.endswith("/"):
                        rmtree(f"{repo.local_path}/{files}")
                    else:
                        remove(f"{repo.local_path}/{files}")
            except KeyError:
                pass
        try:
            if boulder_config["manifest"]["generate-for-build"] or dev_mode:
                console.log("Generating manifest...")
                if "behaviour_pack" in boulder_config["folders"]:
                    generate_manifest("behaviour_pack")
                if "resource_pack" in boulder_config["folders"]:
                    generate_manifest("resource_pack")
                console.log("Manifest generated!")
        except KeyError:
            pass
        os.chdir(boulder_path())
        if dev_mode:
            console.log("Moving to development folder")
            if "behaviour_pack" in boulder_config["folders"]:
                try:
                    rmtree(
                        f"{global_config["minecraft_path"]}/development_behavior_packs/{boulder_config['manifest']['name']}"
                    )
                except FileNotFoundError:
                    pass
                move(
                    f"{boulder_path}/build/{boulder_config['manifest']['name']}/{boulder_config["folders"]["behaviour_pack"]}",
                    f"{global_config["minecraft_path"]}/development_behavior_packs/{boulder_config['manifest']['name']}",
                )
            if "resource_pack" in boulder_config["folders"]:
                try:
                    rmtree(
                        f"{global_config["minecraft_path"]}/development_resource_packs/{boulder_config['manifest']['name']}"
                    )
                except FileNotFoundError:
                    pass
                move(
                    f"{boulder_path}/build/{boulder_config['manifest']['name']}/{boulder_config["folders"]["resource_pack"]}",
                    f"{global_config["minecraft_path"]}/development_resource_packs/{boulder_config['manifest']['name']}",
                )
        else:
            console.log("Moving to build folder")
            try:
                rmtree(f"{project_path()}/{boulder_config["folders"]["build"]}/")
            except FileNotFoundError:
                pass
            copytree(
                f"{boulder_path}/build/{boulder_config['manifest']['name']}",
                f"{project_path()}/{boulder_config["folders"]["build"]}/",
            )
            rmtree(f"{boulder_path}/build/{boulder_config['manifest']['name']}")
        console.log("Build complete!")
    except KeyError:
        console.error("Hook format is invalid!")
        console.tip("Try making a hook with boulder instead of manually!")
        exit(1)
    except BuildIssue as e:
        console.error(e, doexit=True)
    except PermissionError as e:
        console.error(
            "Ensure that any program that locks a folder (cmd/terminal) is closed!"
        )
        console.error(e, doexit=True)


def generate_manifest(pack_type):
    try:
        dump_json(
            f"{boulder_path()}/build/{boulder_config['manifest']['name']}/{boulder_config['folders'][pack_type]}/manifest.json",
            {},
        )
        if os.path.exists(f"{boulder_path()}/build/cached_uuid.json"):
            cached_uuid = load_json(f"{boulder_path()}/build/cached_uuid.json")
        else:
            cached_uuid = {}
        try:
            uuid_header = cached_uuid[boulder_config["manifest"]["name"]][
                f"{pack_type}/header"
            ]
        except KeyError:
            uuid_header = str(uuid4())
            cached_uuid[boulder_config["manifest"]["name"]][
                f"{pack_type}/header"
            ] = uuid_header
        try:
            uuid_modules = cached_uuid[boulder_config["manifest"]["name"]][
                f"{pack_type}/modules"
            ]
        except KeyError:
            uuid_modules = str(uuid4())
            cached_uuid[boulder_config["manifest"]["name"]][
                f"{pack_type}/modules"
            ] = uuid_modules
        manifest = template_manifest
        manifest["header"] = {
            "name": boulder_config["manifest"]["name"],
            "description": boulder_config["manifest"]["description"],
            "uuid": uuid_header,
            "version": list(map(int, boulder_config["manifest"]["version"].split("."))),
            "min_engine_version": list(
                map(int, boulder_config["manifest"]["min_engine_version"].split("."))
            ),
        }
        manifest["modules"].append(
            {
                "type": "data" if pack_type == "behaviour_pack" else "resource",
                "description": boulder_config["manifest"]["description"],
                "uuid": uuid_modules,
                "version": list(
                    map(int, boulder_config["manifest"]["version"].split("."))
                ),
            }
        )
        for dependency in boulder_config["manifest"]["dependencies"][pack_type]:
            manifest["dependencies"].append(dependency)
            manifest["dependencies"].append(
                {"uuid": str(uuid4()), "version": [1, 0, 0]}
            )
        for module in boulder_config["manifest"]["modules"][pack_type]:
            module["uuid"] = str(uuid4())
            manifest["modules"].append(module)
        dump_json(
            f"{boulder_path()}/build/{boulder_config['manifest']['name']}/{boulder_config['folders'][pack_type]}/manifest.json",
            manifest,
        )
        dump_json(f"{boulder_path()}/build/cached_uuid.json", cached_uuid)
    except KeyError:
        console.error("Manifest format is invalid!")
        exit(1)
