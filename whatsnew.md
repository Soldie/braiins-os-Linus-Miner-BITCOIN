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
