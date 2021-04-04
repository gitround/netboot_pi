import tarfile, requests
#import parted  # type: ignore
import subprocess, os, time, shutil
import psutil  # type: ignore
from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from sys import exit, argv, stdout
from typing import List, Dict
from rich.prompt import Prompt
from tqdm import tqdm  # type: ignore


if os.geteuid() != 0:
    print(f"[red]this script requires root privileges. Maybe try: sudo {argv[0]}[/]")
    exit(1)

global bad_disks
bad_disks: List[str] = []
for disk in psutil.disk_partitions():
    bad_disks.append(disk.device)


def pxeify(convert: bool = False, target=None):
    is_sd_card = Prompt.ask(
        "Is the device you are using as the boot media a SD card or a USB flash drive",
        choices=["Y", "N"],
    )
    if is_sd_card == "N":
        subprocess.run("sed -i 's/mmcblk0/sda1/g boot/cmdline.txt", shell=True)
        subprocess.run("sed -i 's/mmcblk0/sda2/g root/etc/fstab", shell=True)
    shutil.copy("second_stage.py", "root/etc/profile.d/")
    os.mkdir("root/scripts")
    shutil.copytree("stage_scripts", "root/scripts")


def download_file(url: str):
    local_filename = url.split("/")[-1]
    filesize = int(requests.head(url).headers["Content-Length"])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            with tqdm(
                unit="B",  # unit string to be displayed.
                unit_scale=True,  # let tqdm to determine the scale in kilo, mega..etc.
                unit_divisor=1024,  # is used when unit_scale is true
                total=filesize,  # the total iteration.
                file=stdout,  # default goes to stderr, this is the display on console.
                desc=local_filename,  # prefix to be displayed on progress bar.
            ) as progress:
                for chunk in r.iter_content(chunk_size=8192):
                    datasize = f.write(chunk)
                    progress.update(datasize)


def check_block(device: Dict[str, str]) -> bool:
    device_id = device["disk"].strip("/dev/")
    root_device = (
        subprocess.check_output(
            f'basename "$(readlink -f "/sys/class/block/{device_id}/..")"', shell=True
        )
        .decode()
        .strip()
    )
    if root_device == "block":
        return True
    return False


def check_mounted(device: Dict[str, str]) -> bool:
    disk = device["disk"]
    for bad_disk in bad_disks:
        if disk in bad_disk:
            return True
    return False


table = Table(title="All safe and usable disks")
table.add_column("id", justify="center", style="red", no_wrap=True)
table.add_column("disk", justify="right", style="green", no_wrap=True)
table.add_column("type", justify="right", style="magenta", no_wrap=True)
table.add_column("size", justify="right", style="magenta", no_wrap=True)
table.add_column("reported model", justify="right", style="cyan", no_wrap=True)

print(
    Panel.fit(
        "[blue bold]Welcome to [bold]pxeboot-pi[/bold] setup\nthis program will setup archlinuxarm on a USB flash drive or SD card of your choice.\nThis will wipe any data on these drives.\nusing pxe boot you can boot other systems of your local network[/]"
    )
)

listdrives = subprocess.Popen(
    "lsblk -o KNAME,TYPE,SIZE,MODEL", shell=True, stdout=subprocess.PIPE
)
output, err = listdrives.communicate()
if err != None:
    print(
        f"[red bold blink] unable to read USV devices. recived following error {err.decode()}"
    )
    exit(1)
devices: List[Dict] = []
device_id = 1
for line in output.decode().split("\n"):
    if line.startswith("KNAME"):
        pass
    else:
        if len(line) != 0:
            device_info = line.split()
            if len(device_info) > 3:
                info = {
                    "disk": f"/dev/{device_info[0]}",
                    "type": device_info[1],
                    "size": device_info[2],
                    "model": device_info[3],
                }
            else:
                info = {
                    "disk": f"/dev/{device_info[0]}",
                    "type": device_info[1],
                    "size": device_info[2],
                    "model": "None",
                }
            if (
                check_block(info) == True
                and info["type"] != "rom"
                and info["type"] != "loop"
                and check_mounted(info) == False
            ):
                devices.append(info)
                table.add_row(
                    str(device_id),
                    info["disk"],
                    info["type"],
                    info["size"],
                    info["model"],
                )
                device_id += 1
if len(devices) == 0:
    print("[red] no usable disks found[/]")
    exit(1)
console = Console()
console.print(table)
disk_id = 0
while disk_id > len(devices) or disk_id < len(devices):
    disk_id = int(
        console.input(
            "enter id of disk to use. [italic bold]this will erase the data on the disk you select[/]: "
        )
    )
target = devices[disk_id - 1]
confirm = Prompt.ask(
    f"[red bold]CREATING PARTIONS. THIS WILL DESTORY ALL DATA ON {target['disk']}. IF YOU DO NOT WANT THIS TO HAPPEN ENTER N[/]",
    choices=["Y", "N"],
)
if confirm == "N":
    print("[green] no changes where made[/]")
    exit(0)
time.sleep(5)
print("[green] creating partions [/green]")
disk = target["disk"].replace("/","\/")
subprocess.check_call(["sed", "-i", f"s/partition_here/'{disk}'/g", "partition.sh"])
subprocess.check_call("bash partition.sh", shell=True)
print("[green]done partitioning disk[/green]")
subprocess.check_call(["lsblk"])
print("[green]formating new partions, this may take a while[/]")

if not os.path.exists("root"):
    os.mkdir("root")
if not os.path.exists("boot"):
    os.mkdir("boot")
if any(os.scandir("root")):
    print(
        "[red]directory root is not empty, exiting. Please empty it before running this again[/red]"
    )
if any(os.scandir("boot")):
    print(
        "[red]directory boot is not empty, exiting. Please empty it before running this again[/red]"
    )

# mount the root partition
subprocess.check_call(["mkfs.vfat",f"{target['disk']}1"])
subprocess.check_call(["mkfs.ext4",f"{target['disk']}2"])
os.system(f"mount {target['disk']}2 root")
# mount boot
os.system(f"mount {target['disk']}1 boot")

available_pis = ["rpi", "rpi-2", "rpi-3", "rpi-4"]
aarch_64_pis = ["rpi-3", "rpi-4"]
rpi_table = Table()
rpi_table.add_column("id", justify="center", style="red", no_wrap=True)
rpi_table.add_column("name", justify="right", style="green", no_wrap=True)
rpi_table.add_column("aarch64 support", justify="right", style="magenta", no_wrap=True)
rpi_id = 1
for pi in available_pis:
    if pi in aarch_64_pis:
        rpi_table.add_row(str(rpi_id), pi, "[green]:heavy_check_mark:[/]")
    else:
        rpi_table.add_row(str(rpi_id), pi, "[red]:x:[/]")
    rpi_id += 1

print(
    Panel.fit(
        "[blue bold]Select your raspberry pi model from those, bellow.\nIf your pi support aarch64 you will be asked to select if you wish to use it.\nusing aarch64 does mean you will not be able to use some proprietary blobs.[/]"
    )
)
console = Console()
console.print(rpi_table)
model_id = int(
    Prompt.ask(
        "[green]Which pi will you be using this with: [/]",
        choices=[str(i) for i in range(1, rpi_id + 1)],
    )
)
aarch64 = ""
choice = "u"
if available_pis[model_id - 1] in aarch_64_pis:
    choice = Prompt.ask(
        "Your pi supports the aarch64 cpu instruction set.\nwould you like to use an aarch64 version of archlinuxarm?",
        choices=["Y", "N"],
    )
    if choice.lower() == "y":
        aarch64 = "-aarch64"
        model_id = 1
file = f"{available_pis[model_id-1]}{aarch64}-latest.tar.gz"
if os.path.exists(file):
    shutil.rmtree(file)
url = f"http://os.archlinuxarm.org/os/ArchLinuxARM-{available_pis[model_id-1]}{aarch64}-latest.tar.gz"
download_file(url)
tar = tarfile.open(file)
tar.extractall("root")
tar.close()
shutil.move("root/boot", "boot")
subprocess.check_call(["sync"])
pxeify(convert=True, target=target)
if available_pis[model_id] == "rpi-4" and aarch64 == "-aarch64":
    os.system("sed -i 's/mmcblk0/mmcblk1/g' root/etc/fstab")
boot_umount = subprocess.Popen(["umount", "-R", "boot"])
root_umount = subprocess.Popen(["umount", "-R", "root"])
if boot_umount.returncode != 0 or root_umount.returncode != 0:
    print("[red] unable to unmount partitions, you should unmount them manually[/]")
    exit(1)
else:
    print("[green bold] the next time you login[/]")
