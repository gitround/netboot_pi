#!/usr/bin/env bash
(
echo g
echo n # Add a new partition
echo 1
echo
echo +512M  # 512 mb size

echo n # Add a new partition
echo 2 # Partition number
echo   # First sector (Accept default: end of last sector)
echo   # Last sector (Accept default: rest of disk)
echo w # Write changes
) | sudo fdisk '/dev/sdc'


