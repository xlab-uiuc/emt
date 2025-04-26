## Mount Extra Disk Guide

This guide walks through the steps to format, mount, and persistently attach a new disk (e.g., /dev/sdb) to /data.

### Step 1: Identify the Disk
--------------------------

Check available disks:

    sudo fdisk -l

Find your target disk (e.g., /dev/sdb) that is not yet partitioned or mounted.

### Step 2: Partition the Disk
--------------------------

    sudo fdisk /dev/sdb

Inside fdisk, follow these prompts:

    n   # Create a new partition
    p   # Primary
    (Accept default partition number, first and last sectors)
    w   # Write changes

### Step 3: Format the Partition
----------------------------

    sudo mkfs.ext4 /dev/sdb1

### Step 4: Create a Mount Point
----------------------------

    sudo mkdir -p /data

### Step 5: Mount the Partition
---------------------------

    sudo mount /dev/sdb1 /data

    # verify
    sudo mount | grep /data

### Step 6: [Optional] Make It Persistent with /etc/fstab 
------------------------------------------

[Only if you want to have disk automatically mounted at boot time]

Get the UUID of the partition:

    sudo blkid

Look for the UUID of /dev/sdb1, e.g.:

    /dev/sdb1: UUID="4a637bf0-43ad-4c2c-bf79-520475203957" TYPE="ext4"

Edit /etc/fstab:

    sudo nano /etc/fstab

Add the following line:

    UUID=4a637bf0-43ad-4c2c-bf79-520475203957 /data ext4 defaults 0 2

Save and exit.

### Step 7: [Optional] Verify Mount Setup
--------------------------

Check if the config is valid:

    sudo findmnt --verify

To test it without rebooting:

    sudo umount /data
    sudo mount -a

If /data is mounted again, the setup is correct.