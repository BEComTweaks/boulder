from subprocess import run
from sys import executable as pyexe
import os
if str(os.getcwd()).endswith("system32"):
		# This has to be in every script to prevent FileNotFoundError
		# Because for some reason, it runs it at C:\Windows\System32
		# Yeah, it is stupid, but I can't put these lines in custom_functons
		# Because that still brings up an error
		os.chdir(os.path.dirname(os.path.realpath(__file__)))

def require(module, module_name=""):
		try:
				__import__(module)
		except ImportError:
				if module_name == "":
						run([pyexe, "-m", "pip", "install", module, "--quiet"])
				else:
						run([pyexe, "-m", "pip", "install", module_name, "--quiet"])

require("colorama")
from colorama import *
require("requests")
import requests
import os
import sys

if os.name == "nt":
		if "HOME" in os.environ and "USERPROFILE" in os.environ:
				terminal_type = "unix"
		else:
				terminal_type = "cmd"
				import winreg
else: 
		terminal_type = "unix"

def print_tag(tag, message):
		if tag == "error":
				print(f"{Back.RED} ERROR {Back.RESET}\t{message}")
		elif tag == "watch":
				print(f"{Back.BLUE} WATCH {Back.RESET}\t{message}")
		elif tag == "dev":
				print(f"{Back.LIGHTBLACK_EX} DEV {Back.RESET}\t{message}")
		elif tag == "warn":
				print(f"{Back.YELLOW} WARN {Back.RESET}\t{message}")
		elif tag == "info":
			  print(f"{Back.CYAN} INFO {Back.RESET}\t{message}")
		else:
				print_tag("error", f"Function `print_tag` does not support tag = {tag}")

# change branch name
remote_url = "https://raw.githubusercontent.com/BEComTweaks/boulder/refs/heads/im-cooking-please-wait/src/"
try:
	response = requests.get(f'{remote_url}/installer/files.json')
	if response.status_code == 200:
		print_tag("info", "Fetched files to install.")
		files = response.json()
		for script in files["python"]:
			response = requests.get(f'{remote_url}/{script}')
			if response.status_code == 200:
				with open(script, "w") as file:
					file.write(response.text)
			else:
				raise requests.exceptions.ConnectionError
		for other_file in files["others"]:
			response = requests.get(f'{remote_url}/{other_file}')
			if response.status_code == 200:
				with open(other_file, "w") as file:
					file.write(response.text)
			else:
				raise requests.exceptions.ConnectionError
		print_tag("info", "Pulled all files")
		new_path = os.path.dirname(__file__)
		if terminal_type == "cmd":
			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
				current_path = winreg.QueryValueEx(key, "Path")[0]
				updated_path = current_path + ";" + new_path
				winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated_path)
			with open("boulder.bat", "w") as script:
				script.write('@echo off\npython "%~dp0boulder.py" %*')
		else:
			print_tag("info", "I need more info on your terminal installation!")
			print_tag("info", "Please input the terminal's type (`bash`, `zsh`, `fish`, etc)")
			terminal_type = input()
			shell_rc = os.path.join(os.environ["HOME"], f".{terminal_type}rc")
			if os.path.exists(shell_rc):
				with open(shell_rc, "a") as file:
					file.write(f"export PATH=$PATH:{new_path}\n")
			else:
				print_tag("error", "Give the Terminal's actual name")
				exit(1)
			with open("boulder", "w") as script:
				script.write('#!/bin/bash\npython "$(dirname "$0")/boulder.py" "$@"')
			os.system("chmod +x boulder")
		os.remove(__file__)
		print_tag("info", "Install successful!")
	else:
		raise requests.exceptions.ConnectionError
except requests.exceptions.ConnectionError:
	print_tag("error", "Failed to fetch files to install.")
	try:
		print_tag("error", f"Status code: {response.status_code}")
	except NameError:
		print_tag("error", "Please connect to an active internet connection.")
	exit(1)