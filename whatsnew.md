## Antminer

- bmminer now supports overt Asic Boost via version rolling, latest bitstream from Bitmain
  has been integrated and BIP310 support has been enabled

- LUCI interface
  - new option to enable Asic Boost
  - provide a way to configure par chain frequencies and voltages

- temperature reporting has been corrected to take measurements from
  the 'middle' sensor that is placed in the hot area of each
  hashboard. The displayed temperatures should better reflect the true
  temperature of the hashboard.

# 2018-09-22-0

## Antminer
- the transitional firmware now supports flashing Antminers S9 in addition to originally supported S9i

### Voltage Control
- web miner configuration interface now allows setting global voltage
  for all chains along with frequency.

## All hardware types

- package list update triggered via web UI doesn't report missing SSL
support error anymore

- opkg no longer reports errors about missing feeds due to an attempt to fetch
