from custom_functions import *
from core import Git, check_repo, boulder_path, project_path

def setHookHandlerVars(config_global, config_boulder, console_instance):
    global global_config
    global boulder_config
    global console
    global_config = config_global
    boulder_config = config_boulder
    console = console_instance

def add_hook(id, url=""):
    import requests

    try:
        if url == "":
            parsed_repo_id = id.split("/")
        else:
            parsed_repo_id = url.split("/")[-2:] + [id]
        if len(parsed_repo_id) == 3:
            response = requests.get(
                f"https://api.github.com/repos/{parsed_repo_id[0]}/{parsed_repo_id[1]}/contents/"
            )
            if response.status_code == 200:
                console.log("Repo exists!")
                id = parsed_repo_id[2]
                # check formatting
                has_hooks = False
                for file_json in response.json():
                    if file_json["name"] == ".boulder_hooks.json":
                        has_hooks = True
                if not has_hooks:
                    raise RepoIssue(["No hooks found", response])
                else:
                    console.log("Repo is properly formatted!")
                    url = f"https://github.com/{parsed_repo_id[0]}/{parsed_repo_id[1]}"
            else:
                raise RepoIssue(["Repo not found", response])
        else:
            console.error("Invalid hook ID!")
            exit(1)
        repo = check_repo({"repo": url}, boulder_path())
        repo_hooks = load_json(f"{repo.local_path}/.boulder_hooks.json")
        console.log("Checking if hook exists...", vb=True)
        for hook in repo_hooks:
            if hook["id"] == id:
                console.log("Hook exists!")
                console.log("Adding to project...")
                hook_list = load_json(f"{boulder_path()}/hooks/hook_list.json")
                repo_to_add = hook_list[url]["checkout"]["at"]
                boulder_config["hooks"]["remote"].append(
                    {
                        "id": id,
                        "repo": url,
                        "checkout": repo_to_add,
                        "checkout_type": "branch",
                    }
                )
                dump_json(f"{project_path()}/boulder_config.json", boulder_config)
                console.log("Hook added!")
                console.tip("You can add extra details ")
    except RepoIssue as ex:
        console.error(str(ex.args[0][0]), show_traceback=False)
        console.error(
            f"Status code {ex.args[0][1].status_code}", vb=True, show_traceback=False
        )
        console.error(f"Received: {ex.args[0][1].text}", vb=True, show_traceback=False)
        exit(1)
