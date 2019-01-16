#!/bin/sh -e

# update system with missing utilities
cp system/ld-musl-armhf.so.1 /lib
chmod +x /lib/ld-musl-armhf.so.1

cp system/fw_printenv /usr/sbin
chmod +x /usr/sbin/fw_printenv

ln -fs /usr/sbin/fw_printenv /usr/sbin/fw_setenv

ETHADDR=$(cat /sys/class/net/eth0/address)

# create hardware id
echo $ETHADDR >/dev/urandom
MINER_HWID=$(dd if=/dev/urandom bs=1 count=12 2>/dev/null | base64 | tr +/ ab)

# change current directory to firmware
cd firmware

# run stage 1 upgrade process
if ! /bin/sh stage1.sh "$MINER_HWID" yes cond no >/dev/null; then
	# clean up system to left it untouched
	rm /usr/sbin/fw_setenv
	rm /usr/sbin/fw_printenv
	rm /lib/ld-musl-armhf.so.1
	exit 1
fi
