#!/bin/sh

# Copyright (C) 2018  Braiins Systems s.r.o.
#
# This file is part of Braiins Build System (BB).
#
# BB is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

set -e

mtd_write() {
	mtd -e "$2" write "$1" "$2"
}

echo "Running stage2 upgrade process..."

ETHADDR=$(fw_printenv -n ethaddr 2> /dev/null)
MINER_HWID=$(fw_printenv -n miner_hwid 2> /dev/null)

# turn off error checking for auxiliary settings
set +e
STAGE3_OFFSET=$(fw_printenv -n stage3_off 2> /dev/null)
STAGE3_SIZE=$(fw_printenv -n stage3_size 2> /dev/null)
STAGE3_MTD=/dev/mtd$(fw_printenv -n stage3_mtd 2> /dev/null)
STAGE3_PATH="/tmp/stage3.tgz"

NET_HOSTNAME=$(fw_printenv -n net_hostname 2> /dev/null)
NET_IP=$(fw_printenv -n net_ip 2> /dev/null)
NET_MASK=$(fw_printenv -n net_mask 2> /dev/null)
NET_GATEWAY=$(fw_printenv -n net_gateway 2> /dev/null)
NET_DNS_SERVERS=$(fw_printenv -n net_dns_servers 2> /dev/null)

MINER_FREQ=$(fw_printenv -n miner_freq 2> /dev/null)
MINER_VOLTAGE=$(fw_printenv -n miner_voltage 2> /dev/null)
MINER_FIXED_FREQ=$(fw_printenv -n miner_fixed_freq 2> /dev/null)
set -e

mtd_write fit.itb recovery
mtd -n -p 0x0800000 write factory.bin.gz recovery
mtd -n -p 0x1400000 write system.bit.gz recovery
mtd -n -p 0x1500000 write boot.bin.gz recovery

mtd_write miner_cfg.bin miner_cfg
fw_setenv -c miner_cfg.config --script - <<-EOF
	# MAC address
	ethaddr=${ETHADDR}
	#
	# network settings
	net_hostname=${NET_HOSTNAME}
	net_ip=${NET_IP}
	net_mask=${NET_MASK}
	net_gateway=${NET_GATEWAY}
	net_dns_servers=${NET_DNS_SERVERS}
	#
	# miner settings
	miner_hwid=${MINER_HWID}
	miner_freq=${MINER_FREQ}
	miner_voltage=${MINER_VOLTAGE}
	miner_fixed_freq=${MINER_FIXED_FREQ}
EOF


if [ -n "${STAGE3_SIZE}" ]; then
	# detected stage3 upgrade tarball
	nanddump -s ${STAGE3_OFFSET} -l ${STAGE3_SIZE} -f "${STAGE3_PATH}" ${STAGE3_MTD}
fi

mtd erase uboot_env
mtd erase fpga1
mtd erase fpga2
mtd erase firmware1
mtd erase firmware2

if [ -n "${STAGE3_SIZE}" ]; then
	# write size of stage3 tarball to the first block of firmware2 partition
	printf "0: %.8x" ${STAGE3_SIZE} | xxd -r -g0 | mtd -n write - firmware2
	# write stage3 upgrade tarball to firmware2 partition after header block
	mtd -n -p 0x0100000 write "${STAGE3_PATH}" firmware2
fi

sync
