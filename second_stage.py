"""pacman""" "-S base-devel python python-gitpython python-requests"
"""python""" "second_stage.py"
exit
# install the deps of this stage before launching it
import subprocess
import shutil
import os
from git import Repo  # type: ignore

if os.geteuid() == 0:
    print("run this script with root permissions")
    exit(1)
subprocess.check_call(
    [
        "sed",
        "--in-place",
        "s/^#\s*\(%wheel\s\+ALL=(ALL)\s\+NOPASSWD:\s\+ALL\)/\1/",
        "/etc/sudoers",
    ]
)
path = os.path.expanduser("~/pxe")
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)
Repo.clone_from("https://aur.archlinux.org/pixiecore-git.git", path)
os.chdir(path)
os.system(f"chown -R alarm {path}")
subprocess.check_call(["su", "-c" "makepkg -si --nocomfirm", "alarm"])
shutil.copy("/scripts/launch-pixiecore.sh", "/usr/bin/")
shutil.copy("/scripts/pxe-launcher.service", "/etc/systemd/system/")
subprocess.check_call(["systemctl", "enable", "pxe-os.service"])
# this script is pretty special.
# its both vaild bash and python :)
