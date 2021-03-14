# PXE boot auto-setup 
I wrote this script over a few days after I accidentally nuked my laptop over a few times over the better part of a week. This script sets up your raspberry pi by installing "stages" of scripts that change configs and install software. The initial script also partitions and install archlinuxarm to your raspberry pi. 

## what is this PXE boot thing?

PXE (Pre eXecution Environment) aka pixie, is a method of booting a computer only using its networking stack(note this does not work for all wifi chipsets, it will work with all internal etherenet ports). Using this we can run a live image on the system. 

Normally one would need to setup some complicated software like [fog](https://fogproject.org/), however [Pixiecore](https://github.com/danderson/netboot/tree/master/pixiecore) simplifies this running the server to one command. Hence these scripts use this to avoid the complications brought by dnsmasq and tftp. 

To get start plug in in the drive you want to boot your raspberry pi off of and run 
```
# python first_stage.py
```
The final stage esstntially launchs pixiecore like so,
```
pixiecore quick arch --dhcp-no-bind
```
this can be changed to a distro of your choice such as ubuntu or fedora. A few files in this project use polyglot code to behave as valid bash and python allowing use to "relaunch" the bash script as a python script.

## compatibility
Currently this project requires libraries not compatible with Mac os and windows. If you do make a version that supports other operating systems feel free to open a pullrequest.

### requirments
The first stage script requires the following libraries
```
rich # user interface
pyparted # partioning disk
requests # downloading the root-fs for archlinuxarm
tqdm # progress bar for downloading in the future will be replaced by rich
libmount # mounting of disk partions
```
you will need to have `util-linux` installed for libmount to work correctly. 
