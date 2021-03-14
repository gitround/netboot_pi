
import subprocess, os, shutil
from git import Repo  # type:ignore

path = os.path.expanduser("~/pxe")
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)
Repo.clone_from("https://aur.archlinux.org/pixiecore-git.git",path)
os.chdir(path)
subprocess.check_call("sudo makepkg -si --nocomfirm", shell=True)
shutil.copy("/scripts/pxe-os.service", "")
subprocess.check_call(["su", "-c","sudo systemctl enable --user pxe-os.service", "alarm"])

