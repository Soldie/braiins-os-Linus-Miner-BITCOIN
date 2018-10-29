# Table of contents

- [Overview](#overview)
- [Initial steps](#initial-steps)
- [Method 1: Creating bootable SD card image  (Antminer S9i example)](#method-1--creating-bootable-sd-card-image---antminer-s9i-example-)
- [Method 2: Migrating from factory firmware to braiins OS](#method-2--migrating-from-factory-firmware-to-braiins-os)
- [Basic user's guide](#basic-user-s-guide)
  * [AsicBoost support](#asicboost-support)
  * [Migrating from braiins OS to factory firmware](#migrating-from-braiins-os-to-factory-firmware)
  * [Recovering bricked (unbootable) devices using SD card](#recovering-bricked--unbootable--devices-using-sd-card)
  * [Firmware upgrade](#firmware-upgrade)
  * [Factory reset (to initial braiins OS version)](#factory-reset--to-initial-braiins-os-version-)

# Overview

This document is a quick-start guide on how to install braiins OS on your mining device using a Linux computer.
There are two ways how to test and use braiins OS:

1. Boot from SD card with braiins OS image, effectively keeping the stock firmware in the built-in flash memory. In case you encounter any issues, you can simply boot the stock firmware from the internal memory. This is a safe way we suggest to start with.

2. Permanently reflash the stock firmware, effectively replacing the manufacturer’s firmware completely with braiins OS. In this method the only way how to go back to the default stock setup is to restore the manufacturer’s firmware from a backup that you create during install.

Due to aforementioned reasons, it is higly recommended to install braiins OS firmware **only on devices with SD card slots**.

You will need:

* supported ASIC miner (see the list below)
* computer with Linux or Windows
* SD card (optional but recommended method)

*Note: Commands used in this manual are instructional. You might need to adjust file paths and names adequately.*

# Initial steps

Download the latest released firmware images + signatures from: [https://feeds.braiins-os.org/](https://feeds.braiins-os.org/)


The table below outlines correspondence between firmware image archive and a particular hardware type.

| Firmware prefix | Hardware |
| --- | --- |
| braiins-os-firmware_zynq-am1-s9_*.tar.bz2 | Antminer S9 |
| braiins-os-firmware_zynq-dm1-g9_*.tar.bz2 | Dragon Mint T1 with G9 control board |
| braiins-os-firmware_zynq-dm1-g19_*.tar.bz2 | Dragon Mint T1 with G19 control board |

You can check the downloaded file for its authenticity and integrity. The image signature can be verified by [GPG](https://www.gnupg.org/documentation/):

```bash
gpg2 --search-keys release@braiins.cz
for i in ./braiins-os-firmware_*.tar.bz2; do gpg2 --verify $i.asc; done
```

You should see something like:

```
gpg: assuming signed data in './braiins-os-firmware_zynq-am1-s9_2018-09-22-0-853643de.tar.bz2'
gpg: Signature made Sat 22 Sep 2018 02:27:03 PM CEST using RSA key ID 616D9548
gpg: Good signature from "Braiins Systems Release Key (Key used for signing software made by Braiins Systems) <release@braiins.cz>" [ultimate]
```

Unpack the firmware image using standard file archiver software (e.g. 7-Zip, WinRAR) or the folllowing command (Linux):

```bash
for i in  ./braiins-os-firmware_*.tar.bz2; do tar xvjf $i; done
```

The downloaded firmware image contains SD card components as well has a transitional firmware that can be flashed into device's on-board flash memory.


# Method 1: Creating bootable SD card image  (Antminer S9i example)

Insert an empty SD card (with minimum capacity of 32 MB) into your computer and flash the image onto the SD card.

### Using software with GUI (Windows, Linux)

* [Download](https://etcher.io/) and run Etcher
* Select the sd.img image
* Select drive (SD card)
* Copy the image to SD card by clicking on *Flash!*


### Using bash (Linux)

Identify SD cards block device (e.g. by ```lsblk```) and run the following commands:

```
cd braiins-os-firmware_am1-s9-latest;
sudo dd if=sd.img of=/dev/your-sd-card-block-device
sync
```

## Adjusting MAC address
If you know the MAC address of your device, mount the SD card and adjust the MAC address. in ```uEnv.txt``` (most desktop Linux systems have automount capabilities once you reinsert the card into your reader). The ```uEnv.txt``` is environment for the bootloader and resides in the first (FAT) partition of the SD card. That way, once the device boots with braiins OS, it would have the same IP address as it had with the factory firmware.

## Booting the device from SD card
- Unmount the SD card
- Adjust jumper to boot from SD card (instead of NAND memory):
   - [Antminer S9](s9)
   - [Dragon Mint T1](dm1)
- Insert it into the device, start the device.
- After a moment, you should be able to access braiins OS interface on device IP address.


# Method 2: Migrating from factory firmware to braiins OS

Once the SD card works, it is very safe to attempt flashing the built-in flash memory as there will always be a way to recover the factory firmware.
Follow the steps below. The tool creates a backup of the original firmware in the ```backup``` folder. It is important to **keep the backup safe** to resolve any potential future issues.

Below are commands to replace original factory firmware with braiins OS. The tool attempts to login to the machine via SSH, therefore you maybe prompted for a password.

## Using Linux

```bash
cd braiins-os-firmware_am1-s9-latest/factory-transition
virtualenv --python=/usr/bin/python3 .env
source .env/bin/activate
pip install -r ./requirements.txt

python3 upgrade2bos.py your-miner-hostname-or-ip
```

## Using Windows

Please install Python first [following this guide](python-win). Then proceed to run the following commands consecutively:

```bash
cd braiins-os-firmware_am1-s9-latest/factory-transition
mkvirtualenv bos
setprojectdir .
pip install -r requirements.txt

python upgrade2bos.py your-miner-hostname-or-ip
deactivate
```

# Basic user's guide

## AsicBoost support

Braiins OS supports overt (version-rolling) AsicBoost in accordance with [BIP310](https://github.com/bitcoin/bips/blob/master/bip-0310.mediawiki).

Trying to use AsicBoost on pool that is not supporting it will result in error message (device will not start mining at all). Please note there is no automatic detection present at the moment, meaning AsicBoost can be only turned on/off manualy.

**Antminer S9**: AsicBoost is **turned on by default** and can be turned off in the Services > CGMiner settings.

**DragonMint T1**: AsicBoost is turned on by default and **cannot be turned off**. The device is incapable of mining efficiently without AsicBoost.

## Migrating from braiins OS to factory firmware

Restoring the original factory firmware requires issuing the command below. Please, note that the previously created backup needs to be available.

- Run (*on Windows, use `python` command instead of `python3`*):

```bash
python3 restore2factory.py backup/backup-id-date/ your-miner-hostname-or-ip
```

## Recovering bricked (unbootable) devices using SD card

If anything goes wrong and your device seems unbootable, you can use the previously created SD card image to recover it (flash the manufacturer’s firmware to the built-in flash memory):

- Follow the steps in *Creating bootable SD card image* to boot the device
- Run (*on Windows, use `python` command instead of `python3`*):
```
cd braiins-os-firmware_am1-s9-latest/factory-transition
python3 restore.py --sd-recovery backup/2ce9c4aab53c-2018-09-19/ your-miner-hostname-or-ip
```

After the script finishes, wait a few minutes and adjust jumper to boot from NAND (internal memory) afterwards.

## Firmware upgrade

Firmware upgrade process uses standard mechanism for installing/upgrading software packages within any OpenWrt based system. Follow the steps below to perform firmware upgrade.

### Upgrade via web interface

Update the repository information by clicking on *Update lists* button in the System > Software menu. In case the button is missing, the system has to be rebooted!

### Upgrade via SSH

```bash
# download latest packages from feeds server
$ opkg update
# try to upgrade to the latest firmware
$ opkg install firmware
```

Since the firmware installation results in reboot, the following output is expected:

```
root@MINER:~# opkg install firmware
Upgrading firmware on root from 2018-09-22-0-853643de to 2018-09-22-1-8d9b127d...
Downloading https://feeds.braiins-os.org/am1-s9/firmware_2018-09-22-1-8d9b127d_arm_cortex-a9_neon.ipk
Running system upgrade...
--2018-09-22 14:23:47--  https://feeds.braiins-os.org/am1-s9/firmware_2018-09-22-1-8d9b127d_arm_cortex-a9_neon.tar
Resolving feeds.braiins-os.org... 104.25.97.101, 104.25.98.101, 2400:cb00:2048:1::6819:6165, ...
Connecting to feeds.braiins-os.org|104.25.97.101|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 10373471 (9.9M) [application/octet-stream]
Saving to: '/tmp/sysupgrade.tar'

/tmp/sysupgrade.tar                     100%[==============================================================================>]   9.89M  10.7MB/s    in 0.9s

2018-09-22 14:23:48 (10.7 MB/s) - '/tmp/sysupgrade.tar' saved [10373471/10373471]

Collected errors:
* opkg_conf_load: Could not lock /var/lock/opkg.lock: Resource temporarily unavailable.
Saving config files...
Connection to 10.33.0.166 closed by remote host.
Connection to 10.33.0.166 closed.
```

## Factory reset (to initial braiins OS version)

Factory reset is as simple as uninstalling the the current firmware package:

```bash
$ opkg remove firmware
```

This effectively downgrades your firmware version to whatever it was when the transition to braiins OS has been done for the first time.
