import os
import shutil
import subprocess
from sys import exit
from git.repo.base import Repo  # type: ignore

path = f"{os.getcwd()}/pxe_staging"
if not os.path.exists(path):
    os.mkdir(path)
elif any(os.scandir(path)):
    print(f"it appears the folder {path} is not empty, clearing it now")
    shutil.rmtree(path)
    os.mkdir(path)
Repo.clone_from("https://aur.archlinux.org/pixiecore-git.git", path)
os.chdir(path)
try:
    subprocess.check_call("makepkg -si  --noconfirm", shell=True)
except Exception as e:
    print(e)
    exit(1)
subprocess.check_call("sudo pixiecore quick arch --dhcp-no-bind", shell=True)
