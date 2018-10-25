#!/usr/bin/env python3

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

import argparse
import tarfile
import shutil
import sys
import os

from miner.ssh import SSHManager
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from glob import glob

USERNAME = 'root'
PASSWORD = None

MINER_CFG_CONFIG = '/tmp/miner_cfg.config'


def mdt_write(ssh, local_path, mtd, name, erase=True, offset=0):
    # prepare mtd arguments
    mtd_args = ['mtd']
    if erase:
        mtd_args.extend(['-e', mtd])
    if offset > 0:
        mtd_args.extend(['-n', '-p', hex(offset)])
    mtd_args.extend(['write', '-', mtd])

    print("Writing {} to NAND partition '{}'...".format(name, mtd))
    with open(local_path, 'rb') as local, ssh.pipe(mtd_args) as remote:
        shutil.copyfileobj(local, remote.stdin)


def mtd_erase(ssh, mtd):
    print("Erasing NAND partition '{}'...".format(mtd))
    ssh.run(['mtd', 'erase', mtd])


def get_env(ssh, name):
    stdout, _ = ssh.run('fw_printenv', '-n', name)
    return next(stdout).strip()


def set_miner_cfg(ssh, name, value):
    ssh.run('fw_setenv', '-c', MINER_CFG_CONFIG, name, str(value))


def firmware_deploy(args, firmware_dir, stage2_dir):
    # get file paths
    boot_bin = os.path.join(firmware_dir, 'boot.bin')
    uboot_img = os.path.join(firmware_dir, 'u-boot.img')
    fit_itb = os.path.join(stage2_dir, 'fit.itb')
    factory_bin_gz = os.path.join(stage2_dir, 'factory.bin.gz')
    system_bit_gz = os.path.join(stage2_dir, 'system.bit.gz')
    boot_bin_gz = os.path.join(stage2_dir, 'boot.bin.gz')
    miner_cfg_bin = os.path.join(stage2_dir, 'miner_cfg.bin')
    miner_cfg_config = os.path.join(stage2_dir, 'miner_cfg.config')

    print("Connecting to remote host...")
    with SSHManager(args.hostname, USERNAME, PASSWORD) as ssh:
        mdt_write(ssh, boot_bin, 'boot', 'SPL')
        mdt_write(ssh, uboot_img, 'uboot', 'U-Boot')
        mdt_write(ssh, fit_itb, 'recovery', 'recovery FIT image')
        mdt_write(ssh, factory_bin_gz, 'recovery', 'factory image', erase=False, offset=0x0800000)
        mdt_write(ssh, system_bit_gz, 'recovery', 'bitstream', erase=False, offset=0x1400000)
        # original firmware has different recovery partition without SPL bootloader
        if os.path.isfile(boot_bin_gz):
            mdt_write(ssh, boot_bin_gz, 'recovery', 'SPL bootloader', erase=False, offset=0x1500000)
        mdt_write(ssh, miner_cfg_bin, 'miner_cfg', 'miner configuration')

        print("Uploading miner configuration file...")
        sftp = ssh.open_sftp()
        sftp.put(miner_cfg_config, MINER_CFG_CONFIG)
        sftp.close()

        # get environment variables for current firmware
        current_fw = int(get_env(ssh, 'firmware'))
        ethaddr = get_env(ssh, 'ethaddr')
        miner_hwid = get_env(ssh, 'miner_hwid')

        print("Setting miner configuration...")
        set_miner_cfg(ssh, 'ethaddr', ethaddr)
        set_miner_cfg(ssh, 'miner_hwid', miner_hwid)

        # erase rest of partitions
        mtds_for_erase = ['fpga1', 'fpga2', 'uboot_env', 'firmware{}'.format((current_fw % 2) + 1)]
        for mtd in mtds_for_erase:
            mtd_erase(ssh, mtd)

        # reboot system to finish upgrade
        print("Rebooting system...")
        ssh.run('sync')
        ssh.run('reboot')


def main(args):
    with TemporaryDirectory() as backup_dir:
        stream = urlopen(Request(args.firmware_url, headers={'User-Agent': 'Mozilla/5.0'}))
        tar = tarfile.open(fileobj=stream, mode='r|*')
        print('Extracting firmware tarball...')
        tar.extractall(path=backup_dir)
        tar.close()
        # find factory_transition with firmware directory
        firmware_dir = glob(os.path.join(backup_dir, '*', 'factory_transition', 'firmware'))[0]
        stage2_dir = os.path.join(firmware_dir, 'stage2')
        os.makedirs(stage2_dir)
        print('Extracting stage2 tarball...')
        tar = tarfile.open(os.path.join(firmware_dir, 'stage2.tgz'))
        tar.extractall(path=stage2_dir)
        tar.close()
        firmware_deploy(args, firmware_dir, stage2_dir)


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('firmware_url',
                        help='URL to tarball with transitional bos firmware')
    parser.add_argument('hostname',
                        help='hostname of miner with bos firmware')

    # parse command line arguments
    args = parser.parse_args(sys.argv[1:])
    main(args)
