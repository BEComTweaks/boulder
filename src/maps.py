from subprocess import run
def shell_caller(script_loc:str):
    mapped = {
        ".py": "python ",
        ".js": "node ",
        ".sh": "bash ",
        ".bat": "cmd ",
        ".nim": "nim c ",
        ".bat": "",
        ".jar": "java -jar "
    }
    if script_loc[-3:] == ".sh":
        run(["chmod", "+x", script_loc])
        return script_loc
    elif script_loc[-3:] == ".exe":
        return NotImplementedError
    else:
        return mapped[script_loc[-3:]] + script_loc