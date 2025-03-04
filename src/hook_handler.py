from custom_functions import *
from core import Git
from core import check_repo as core_check_repo


def setHookHandlerVars(config_global, config_boulder, console_instance):
    global global_config
    global boulder_config
    global console
    global_config = config_global
    boulder_config = config_boulder
    console = console_instance


def check_repo(url_or_id):
    if "http" in url_or_id:
        console.log("Is a URL", vb=True)
        output = run(["git", "ls-remote", "--exit-code", url_or_id])
        if output.returncode == 0:
            repo = url_or_id.split("/")[-2:]
            console.log("Repo exists!", vb=True)
        else:
            raise RepoIssue(["Repo not found", output])
    elif url_or_id.count("/") == 2:

        """
        If input is gh:BEComTweaks/boulder_hooks/default-commands
        1. Split by : to get ["gh", "BEComTweaks/boulder_hooks/default-commands"]
        2. Remove gh
        3. Split by / to get ["BEComTweaks", "boulder_hooks", "default-commands"]
        4. Remove the last hook
        5. Join by / to get "BEComTweaks/boulder_hooks"
        """
        repo = "/".join(url_or_id.split(":")[-1].split("/")[:-1])
        if "gh:" in url_or_id:
            output = run(
                ["git", "ls-remote", "--exit-code", f"https://github.com/{repo}"]
            )
        elif "cb:" in url_or_id:
            output = run(
                ["git", "ls-remote", "--exit-code", f"https://codeberg.org/{repo}"]
            )
        # elif "gl:" in url_or_id:
        #    output = run(["git", "ls-remote", "--exit-code", f"https://gitlab.com/{repo}"])
        try:
            if output.returncode == 0:
                console.log("Repo exists!", vb=True)
                pass
            else:
                raise RepoIssue(["Repo not found", output])
        except NameError:
            raise RepoIssue(["Hosting identifier not found", output])
    else:
        console.error("Formatting is incorrect!", doexit=True)
    # now check if the repo has the hooks
    if "gh:" in url_or_id or "github.com" in url_or_id:
        response = requests.get(f"https://api.github.com/repos/{repo}/contents/")
    elif "cb:" in url_or_id or "codeberg.org" in url_or_id:
        response = requests.get(f"https://codeberg.org/api/v1/repos/{repo}/contents")
    # elif "gl:" in url_or_id:
    #    response = requests.get(f"https://gitlab.com/{repo}/contents/")
    for file in response.json():
        if file["name"] == ".boulder_hooks.json":
            console.log("Repo has hooks!", vb=True)
            return file
    raise RepoIssue(["No hooks found", response])


def add_hook(args):
    import requests

    received = [None, 0]
    for arg in args:
        if "http" in arg:  # received a url
            received = ["url", args.index(arg)]
        elif ":" in arg:  # supports <host>:<owner>/<repo>/<id>
            # host can so far only be gh or cb (need help with gitlab)
            # pr when needed
            received = ["full_id", args.index(arg)]
    if received[0] == "url":
        response = requests.get(f"{args[received[1]]}")
        if response.status_code == 200:
            response = response.text.lower()
            if "not found" in response:
                raise RepoIssue(["Repo not found", response])
    if received[0] == None:
        received = ["id", 0]
    else:
        # check if hook exists
        download_url = check_repo(args[received[1]])["download_url"]
        response = requests.get(download_url)
        if response.status_code == 200:
            hook_list = response.json()
            exists = False
            for hook in hook_list:
                if received[0] == "url":
                    if args[received[1] + 1] == hook["id"]:
                        exists = True
                        break
                elif received[0] == "full_id":
                    if args[received[1]].split("/")[-1] == hook["id"]:
                        exists = True
                        break
            if not exists:
                raise RepoIssue(["Hook not found", response])
            else:
                console.log("Hook exists in repo!", vb=True)
        else:
            raise RepoIssue(["Failed to get hooks", response])
        # hook exists, now clone
        if received[0] == "url":
            url = args[received[1]]
            id = args[received[1] + 1]
        elif received[0] == "full_id":
            repo = "/".join(args[received[1]].split(":")[-1].split("/")[:-1])
            id = args[received[1]].split(":")[-1].split("/")[-1]
            if "gh:" in args[received[1]]:
                url = f"https://github.com/{repo}"
            elif "cb:" in args[received[1]]:
                url = f"https://codeberg.org/{repo}"
        if received[0] != None:
            repo = core_check_repo({"repo": url})
            project_config = load_boulder_config()
            project_config["hooks"]["remote"].append(
                {
                    "id": id,
                    "repo": url,
                    "checkout_type": "branch",
                    "checkout": repo.branch,
                }
            )
            dump_json(f"{project_path()}/boulder_config.json", project_config)
            console.log("Hook added to project!")


def remove_hook(args):
    # format: remove <id>
    project_config = load_boulder_config()
    while True:
        do_delete = console.input("Are you sure? This cannot be undone! (y/n): ")
        if do_delete.lower() in ["y", "yes", "n", "no"]:
            break
    if do_delete.lower() in ["n", "no"]:
        console.log("Aborted!")
        return
    for hook in project_config["hooks"]["remote"]:
        if args[0] == hook["id"]:
            project_config["hooks"]["remote"].remove(hook)
            dump_json(f"{project_path()}/boulder_config.json", project_config)
            console.log("Hook removed from project!")
            return


def checkout(args):
    # format: <id> checkout <type> <branch>
    project_config = load_boulder_config()
    for hook in project_config["hooks"]["remote"]:
        if args[0] == hook["id"]:
            repo = core_check_repo(hook)
            try:
                output = repo.checkout(args[2], args[3])
            except IndexError:
                if args[2] not in ["branch", "tag", "commit"]:
                    console.warn("Assuming you are not checking out a tag")
                    args.append(args[2])
                    args[2] = "branch"
                    output = repo.checkout("branch", args[3])
            if output.success:
                console.log("Checkout successful!")
                project_config["hooks"]["remote"][
                    project_config["hooks"]["remote"].index(hook)
                ]["checkout_type"] = args[2]
                project_config["hooks"]["remote"][
                    project_config["hooks"]["remote"].index(hook)
                ]["checkout"] = args[3]
                dump_json(f"{project_path()}/boulder_config.json", project_config)
            else:
                console.error("Checkout failed!")
                console.error(output.output, vb=True, doexit=True)


def list_hooks():
    print()
    project_config = load_boulder_config()
    for hook in project_config["hooks"]["remote"]:
        console.config(
            f"ID:\t\t{hook['id']}\nRepo:\t\t{hook['repo']}\nCheckout type:\t{hook['checkout_type']}\nCheckout:\t{hook['checkout']}"
        )
        print()


def help():
    console.config("Commands:")
    console.config("add\n\t\tAdd a hook to the project")
    console.config("\tFormat:\tadd <url> <id>\n\t\tadd <host>:<owner>/<repo>/<id>")
    console.config(
        "      Example:\tadd https://github.com/BEComTweaks/boulder_hooks/ empty"
    )
    console.config("\t\tadd gh:BEComTweaks/boulder_hooks/empty")
    console.config("remove <id>\n\tRemove a hook from the project")
    console.config("list\n\tList all hooks in the project")
    console.config(
        "<id> checkout <type> <branch>\n\tCheckout a branch/tag/commit from a hook"
    )
    console.config("help\n\tShow this help message")
    console.config("switch <id>\n\tSwitch to a different branch/tag/commit from a hook")
