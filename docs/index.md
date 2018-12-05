# Table of contents

   * [Overview](#overview)
   * [Braiins OS Versioning Scheme](#braiins-os-versioning-scheme)
   * [Installing Braiins OS for the First Time (Replacing Factory Firmware with Braiins OS)](#installing-braiins-os-for-the-first-time-replacing-factory-firmware-with-braiins-os)
      * [Initial Steps](#initial-steps)
      * [Phase 1: Creating Bootable SD Card Image (Antminer S9 example)](#phase-1-creating-bootable-sd-card-image-antminer-s9-example)
      * [Phase 2: Permanently Migrating from Factory Firmware to Braiins OS](#phase-2-permanently-migrating-from-factory-firmware-to-braiins-os)
   * [Basic user's guide](#basic-users-guide)
      * [Miner Signalization (LED)](#miner-signalization-led)
         * [Recovery Mode](#recovery-mode)
         * [Normal Mode](#normal-mode)
         * [Identifying a miner in a farm](#identifying-a-miner-in-a-farm)
      * [AsicBoost support](#asicboost-support)
      * [Migrating from Braiins OS to factory firmware](#migrating-from-braiins-os-to-factory-firmware)
      * [Recovering Bricked (unbootable) Devices Using SD Card](#recovering-bricked-unbootable-devices-using-sd-card)
      * [Firmware upgrade](#firmware-upgrade)
         * [Upgrade via web interface](#upgrade-via-web-interface)
         * [Upgrade via SSH](#upgrade-via-ssh)
      * [Reset to initial Braiins OS version](#reset-to-initial-braiins-os-version)
      * [Recovery Mode](#recovery-mode-1)


# Overview

This document is a quick-start guide on how to install Braiins OS on your mining device.
There are two ways how to test and use Braiins OS:

1. **Boot from SD card** with Braiins OS image, effectively keeping the stock firmware in the built-in flash memory. In case you encounter any issues, you can simply boot the stock firmware from the internal memory. This is a safe way we suggest to start with.

2. **Permanently reflash the stock firmware**, effectively replacing the manufacturer’s firmware completely with Braiins OS. In this method the only way how to go back to the default stock setup is to restore the manufacturer’s firmware from a backup that you create during install.

Due to aforementioned reasons, it is highly recommended to install Braiins OS firmware **only on devices with SD card slots**.

You will need:

* supported ASIC miner (see the list below)
* computer with Linux or Windows
* SD card (optional but recommended method)

*Note: Commands used in this manual are instructional. You might need to adjust file paths and names adequately.*

# Braiins OS Versioning Scheme

Each release contains a version number that consists of YYYY-MM-DD-P, where:

| Field | Meaning |
| --- | --- |
| YYYY | 4 digit release year |
| MM | 2 digit month |
| DD | 2 digit day number |
| P | single digit patch level - in case there was a hot fix re-release on the same day |

The version number is also encoded in all artifacts that are available for download.

In addition to the above, each major Braiins OS release has a code name (e.g. wolfram, hafnium, etc.).

## Transitional firmwares

The table below outlines correspondence between transitional firmware image archives (as provided at [https://feeds.braiins-os.org/](https://feeds.braiins-os.org/)) and a particular hardware type.

| Firmware prefix | Hardware |
| --- | --- |
| braiins-os_am1-s9_*.tar.bz2 | Antminer S9, S9i, S9j, R4 |
| braiins-os_dm1-g9_*.tar.bz2 | Dragon Mint T1 with G9 control board |
| braiins-os_dm1-g19_*.tar.bz2 | Dragon Mint T1 with G19 control board |

# Installing Braiins OS for the First Time (Replacing Factory Firmware with Braiins OS)

The steps describe below need to be done only **the very first time** you are installing Braiins OS on a device. You will be using so called *transitional firmware images* mentioned above for this purpose.

## Initial Steps

Download the latest released transitional firmware images + signatures from: [https://feeds.braiins-os.org/](https://feeds.braiins-os.org/)


You can check the downloaded file for its authenticity and integrity. The image signature can be verified by [GPG](https://www.gnupg.org/documentation/):

```bash
gpg2 --search-keys release@braiins.cz
for i in ./braiins-os_*asc; do gpg2 --verify $i; done
```

You should see something like:

```
gpg: assuming signed data in './braiins-os_am1-s9_2018-10-24-0-9e5687a2.tar.bz2'
.
.
gpg: Good signature from "Braiins Systems Release Key (Key used for signing software made by Braiins Systems) <release@braiins.cz>" [ultimate]
```

Unpack the selected (or all) transitional firmware images using standard file archiver software (e.g. 7-Zip, WinRAR) or the following command (Linux):

```bash
for i in  ./braiins-os_*.tar.bz2; do tar xvjf $i; done
```

### Transitional firmware image types

The table below explains the use of individual transitional firmware images

| Firmware prefix | Hardware |
| --- | --- |
| braiins-os_HARDWARE_TYPE_**sd**_VERSION.img | SD card image for testing on hardware, recovering a *bricked* machine etc. |
| braiins-os_HARDWARE_TYPE_**ssh**_VERSION.tar.bz2 | transitional firmware for upgrading from factory firmware that has **ssh** access |
| braiins-os_HARDWARE_TYPE_**telnet**_VERSION.tar.bz2 | transitional firmware for upgrading from factory firmware that provides **telnet** access |
| braiins-os_HARDWARE_TYPE_**web**_VERSION.{vendor specific extension} | transitional firmware for upgrading from factory firmware via the **factory firmware web interface**. The exact file extension depends on particular hardware type |


## Phase 1: Creating Bootable SD Card Image (Antminer S9 example)

Insert an empty SD card (with minimum capacity of 32 MB) into your computer and flash the image onto the SD card.

### Using software with GUI (Windows, Linux)

* [Download](https://etcher.io/) and run Etcher
* Select the sd.img image
* Select drive (SD card)
* Copy the image to SD card by clicking on *Flash!*


### Using bash (Linux)

Identify SD cards block device (e.g. by ```lsblk```) and run the following commands (replace ```VERSION``` with the current latest release):

```
sudo dd if=braiins-os_am1-s9_sd_VERSION.img of=/dev/your-sd-card-block-device
sync
```

### Adjusting MAC Address
If you know the MAC address of your device, mount the SD card and adjust the MAC address. in ```uEnv.txt``` (most desktop Linux systems have automount capabilities once you reinsert the card into your reader). The ```uEnv.txt``` is environment for the bootloader and resides in the first (FAT) partition of the SD card. That way, once the device boots with Braiins OS, it would have the same IP address as it had with the factory firmware.

### Booting the Device from SD Card
- Unmount the SD card
- Adjust jumper to boot from SD card (instead of NAND memory):
   - [Antminer S9](s9)
   - [Dragon Mint T1](dm1)
- Insert it into the device, start the device.
- After a moment, you should be able to access Braiins OS interface on device IP address.


## Phase 2: Permanently Migrating from Factory Firmware to Braiins OS

Once the SD card works, it is very safe to attempt flashing the built-in flash memory as there will always be a way to recover the factory firmware.
Follow the steps below. The tool creates a backup of the original firmware in the ```backup``` folder. It is important to **keep the backup safe** to resolve any potential future issues.

Below are commands to replace original factory firmware with Braiins OS using the SSH variant. The tool attempts to login to the machine via SSH, therefore you maybe prompted for a password.

### Using Linux

```bash
cd braiins-os_am1-s9_ssh_VERSION
virtualenv --python=/usr/bin/python3 .env
source .env/bin/activate
pip install -r ./requirements.txt

python3 upgrade2bos.py your-miner-hostname-or-ip
```

### Using Windows

Please install Python first [following this guide](python-win). Then proceed to run the following commands consecutively:

```bash
cd braiins-os_am1-s9_ssh_VERSION

# create bos environment if it does not exist
mkvirtualenv bos
setprojectdir .

# select bos environment if it has been created already
workon bos

pip install -r requirements.txt

python upgrade2bos.py your-miner-hostname-or-ip
deactivate
```

# Basic user's guide

## Miner Signalization (LED)

Miner LED signalization depends on its operational mode. There are two modes (*recovery* and *normal*) which are signaled by the **green** and **red LED** on the front panel. The LED on the control board (inside) always shows *heartbeat* (flashes at a load average based rate).


### Recovery Mode

The recovery mode is signaled by **flashing green LED** (50 ms on, 950 ms off) on the front panel. The **red LED** represents access to a NAND
disk and flashing during factory reset when data is written to NAND.

### Normal Mode

The normal mode state is signaled by the combination of the front panel **red** and **green LED** as specified in the table below:

| red LED | green LED | meaning |
| ------- | --------- | ------- |
| on | off | *cgminer* or *cgminer_monitor* are not running |
| slow flashing | off | hash rate is below 80% of expected hash rate or the miner cannot connect to any pool (all pools are dead) |
| off | very slow flashing (1 sec on, 1 sec off) | *miner* is operational and hash rate above 80 % of expected hash rate |
| fast flashing | N/A | LED override requested by user (`miner fault_light on`) |

### Identifying a miner in a farm

The local miner utility can also be used to identify a particular device by enabling aggressive blinking of **red LED**:

```bash
$ miner fault_light on
```

Similarly to disable the LED run:

```bash
$ miner fault_light off
```

## AsicBoost support

Braiins OS supports overt (version-rolling) AsicBoost in accordance with [BIP310](https://github.com/bitcoin/bips/blob/master/bip-0310.mediawiki).

Trying to use AsicBoost on pool that is not supporting it will result in error message (device will not start mining at all). Please note there is no automatic detection present at the moment, meaning AsicBoost can be only turned on/off manually.

### Antminer S9

AsicBoost is **turned on by default**. This setting can be changed in:

- web interface Services > CGMiner menu
- config file ```/etc/cgminer.conf``` by altering the ```multi-version``` value to `1` (disabled) or `4` (enabled)

### DragonMint T1

AsicBoost is **turned on by default** and **cannot be turned off**. The device is incapable of mining efficiently without AsicBoost.

## Migrating from Braiins OS to factory firmware

Restoring the original factory firmware requires issuing the command below. Please, note that the previously created backup needs to be available.

- Run (*on Windows, use `python` command instead of `python3`*):

```bash
python3 restore2factory.py backup/backup-id-date/ your-miner-hostname-or-ip
```

## Recovering Bricked (unbootable) Devices Using SD Card

If anything goes wrong and your device seems unbootable, you can use the previously created SD card image to recover original firmware from the  manufacturer:

- Follow the steps in *Creating Bootable SD Card Image* to boot the device
- Run (*on Windows, use `python` command instead of `python3`*):
```
cd braiins-os_am1-s9_ssh_VERSION
python3 restore2factory.py backup/2ce9c4aab53c-2018-09-19/ your-miner-hostname-or-ip
```

After the script finishes, wait a few minutes and adjust jumper to boot from NAND (internal memory) afterwards.

## Firmware upgrade

Firmware upgrade process uses standard mechanism for installing/upgrading software packages within any OpenWrt based system. Follow the steps below to perform firmware upgrade.

### Upgrade via web interface

- Update the repository information by clicking on *Update lists* button in the System > Software menu. In case the button is missing, the system has to be rebooted!
- Once done, proceed to update the ```firmware``` package.

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

## Reset to initial Braiins OS version

Uninstall the current firmware package to downgrade your firmware to the version which was initially installed when replacing the stock firmware.

```bash
$ opkg remove firmware
```

In addition to the above, reset to initial Braiins OS version can also be initiated as follows:

* *IP SET button* - hold it for *10s* until red LED flashes
* *SD card* - first partition with FAT contains file *uEnv.txt* with a line **factory_reset=yes**
* *miner utility* - call ```miner factory_reset``` from the miner's command line

## Recovery Mode

Users doesn't have to typically enter recovery mode while using Braiins OS in a standard way. The ```bos2factory.py``` downgrade process uses it to restore the original factory firmware from the manufacturer. It can also be useful when repairing/investigating the currently installed system.

The recovery mode can be invoked by different ways:

* *IP SET button* - hold it for *3s* until green LED flashes
* *SD card* - first partition with FAT contains file *uEnv.txt* with a line **recovery=yes**
* *miner utility* - call ```miner run_recovery``` from the miner's command line
