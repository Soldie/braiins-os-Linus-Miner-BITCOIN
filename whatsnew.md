# 2018-11-27-0

## Overview - major release; code name: Cobalt

A new major release that brings important features for S9's and unifies miner status page for all supported devices.

## Antminer S9

- [feature] per chip frequency tuning based on factory calibration constants
- [feature] alternative transitional firmware (```braiins-os_am1-s9_web_*tar.gz```) image that can be flashed via **factory
  web interface**
- [feature] support for S9j and R4 hardware types

## All mining hardware types

- [feature] new **miner overview** page with real-time telemetry data
- [feature] hash rate averaging exponential decay function in cgminer replaced with windowed average
- [feature] login text now indicates when running in recovery mode
- [feature] factory transition firmware preserves network settings of the original firmware. Optionally, user may request keeping the hostname, too (`upgrade2bos.py --keep-hostname`).
- [feature] bOS mode and version are now stored in `/etc/bos_{mode,version}`
- [feature] *upgrade2bos.py* can now skip NAND backup entirely and provide *configuration backup only*. The reason is to save space and speed up the process of upgrading big farms in bulk. The reverse script *restore2factory.py* can take the original factory image and combine it with the saved configuration. Thus, eliminating the need for full NAND backups completely.
- [feature] restore2factory now automatically detects when being run from SD card and acts accordingly
- [feature] new LED signalization scheme - see user documentation for details

### cgminer API improvements

- [feature] support for HTTP GET requests
- [feature] calculation of hourly hardware error rate
- [feature] Asic Boost status (yes/no)
- [feature] hashrate statistics for 1m, 15m, 24h using windowed average


# 2018-10-24-0

## Overview

*This release only contains images for Antminer S9.*

**Important:** If you wish to upgrade firmware (package `firmware`) via the web interface, it is neccesary to install package `libustream-openssl` first. This step is not required when upgrading via SSH.

## Antminer S9

- [feature] bmminer now supports overt **AsicBoost** via version rolling, latest bitstream from Bitmain
  has been integrated and [BIP310](https://github.com/bitcoin/bips/blob/master/bip-0310.mediawiki) support has been enabled. AsicBoost can be turned off in the interface.
- [feature] the transitional firmware now supports **flashing Antminers S9** in addition to originally supported S9i
- [feature] **per chain** frequency and **voltage control** now available in the interface
- [fix] Temperature reporting has been corrected to take measurements from
  the 'middle' sensor that is placed in the hot area of each
  hashboard. The displayed temperatures should better reflect the true
  temperature of the hashboard.

## All hardware types

- [fix] package list update triggered via web UI doesn't report missing SSL support error anymore
- [fix] opkg no longer reports errors about missing feeds due to an attempt to fetch
- [fix] Firmware reports its real release version during stratum subscribe. The default cgminer version has been removed.
