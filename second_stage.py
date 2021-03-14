"""python""" "second_stage.py"
exit
import subprocess
import shutil

subprocess.check_call(
    [
        "pacman",
        "-S",
        "sudo base-devel",
        "--noconfirm",
        "python-gitpython",
        "python-requests",
    ]
)
subprocess.check_call(
    [
        "sed",
        "--in-place",
        "'s/^#\s*\(%wheel\s\+ALL=(ALL)\s\+NOPASSWD:\s\+ALL\)/\1/'",
        "/etc/sudoers",
    ]
)
shutil.move("/pxe_scripts/prep.py", "/etc/profile/")
shutil.rmtree(__file__)
# this script is pretty special.
# its both vaild bash and python :)
