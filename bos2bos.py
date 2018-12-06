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
import subprocess
import tarfile
import shutil
import miner
import sys
import os
import io

import miner.nand as nand

from miner.ssh import SSHManager, SSHError
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from glob import glob

USERNAME = 'root'
PASSWORD = None

MODE_SD = 'sd'
MODE_NAND = 'nand'
MODE_RECOVERY = 'recovery'

MINER_CFG_CONFIG = '/tmp/miner_cfg.config'


class RestoreStop(Exception):
    pass


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


def get_mode(ssh):
    try:
        stdout, _ = ssh.run('cat', '/etc/bos_mode')
        return next(stdout).strip()
    except subprocess.CalledProcessError:
        # fallback for old releases
        try:
            ssh.run('test', '-c', '/dev/ubi0')
        except subprocess.CalledProcessError:
            # SD or recovery mode (NAND can be fully accessed)
            return MODE_SD
        else:
            return MODE_NAND


def get_env(ssh, name):
    stdout, _ = ssh.run('fw_printenv', '-n', name)
    return next(stdout).strip()


def get_ethaddr(ssh):
    stdout, _ = ssh.run('cat', '/sys/class/net/eth0/address')
    return next(stdout).strip()


def check_miner_cfg(ssh):
    _, stderr = ssh.run('fw_printenv', '-c', MINER_CFG_CONFIG)
    for _ in stderr:
        return False
    else:
        return True


def set_miner_cfg(ssh, config, rewrite_miner_cfg):
    miner_cfg_input = io.BytesIO()
    if not nand.write_miner_cfg_input(config, miner_cfg_input, use_default=rewrite_miner_cfg):
        raise RestoreStop
    miner_cfg_input = miner_cfg_input.getvalue()

    if len(miner_cfg_input):
        if rewrite_miner_cfg:
            print("Setting default miner configuration...")
        else:
            print("Overriding miner configuration...")
        # write miner configuration to NAND
        with ssh.pipe('fw_setenv', '-c', MINER_CFG_CONFIG, '-s', '-') as remote:
            remote.stdin.write(miner_cfg_input)


def get_config(args, ssh, rewrite_miner_cfg):
    config = miner.load_config(args.config)

    config.setdefault('miner', miner.EmptyDict())
    config.setdefault('net', miner.EmptyDict())

    if args.mac:
        config.net.mac = args.mac
    elif rewrite_miner_cfg and not config.net.get('mac'):
        config.net.mac = get_ethaddr(ssh)

    return config


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
        # detect mode
        mode = get_mode(ssh)
        print("Detected bOS mode: {}".format(mode))

        print("Uploading miner configuration file...")
        sftp = ssh.open_sftp()
        sftp.put(miner_cfg_config, MINER_CFG_CONFIG)
        sftp.close()

        rewrite_miner_cfg = not check_miner_cfg(ssh)
        config = get_config(args, ssh, rewrite_miner_cfg)

        mdt_write(ssh, boot_bin, 'boot', 'SPL')
        mdt_write(ssh, uboot_img, 'uboot', 'U-Boot')
        mdt_write(ssh, fit_itb, 'recovery', 'recovery FIT image')
        mdt_write(ssh, factory_bin_gz, 'recovery', 'factory image', erase=False, offset=0x0800000)
        mdt_write(ssh, system_bit_gz, 'recovery', 'bitstream', erase=False, offset=0x1400000)
        # original firmware has different recovery partition without SPL bootloader
        if os.path.isfile(boot_bin_gz):
            mdt_write(ssh, boot_bin_gz, 'recovery', 'SPL bootloader', erase=False, offset=0x1500000)
        if rewrite_miner_cfg:
            mdt_write(ssh, miner_cfg_bin, 'miner_cfg', 'miner configuration')

        # set miner configuration
        set_miner_cfg(ssh, config, rewrite_miner_cfg)

        # erase rest of partitions
        mtds_for_erase = ['fpga1', 'fpga2', 'uboot_env']
        if mode == MODE_NAND:
            # active partition cannot be erased
            current_fw = int(get_env(ssh, 'firmware'))
            mtds_for_erase.append('firmware{}'.format((current_fw % 2) + 1))
        else:
            mtds_for_erase.extend(['firmware1', 'firmware2'])

        for mtd in mtds_for_erase:
            mtd_erase(ssh, mtd)

        ssh.run('sync')

        if mode == MODE_SD:
            print('Halting system...')
            print('Please turn off the miner and change jumper to boot it from NAND!')
            ssh.run('halt')
        else:
            print('Rebooting to restored firmware...')
            ssh.run('reboot')


def main(args):
    with TemporaryDirectory() as backup_dir:
        stream = urlopen(Request(args.firmware_url, headers={'User-Agent': 'Mozilla/5.0'}))
        tar = tarfile.open(fileobj=stream, mode='r|*')
        print('Extracting firmware tarball...')
        tar.extractall(path=backup_dir)
        tar.close()
        stream.close()
        # find factory_transition with firmware directory
        firmware_dir = glob(os.path.join(backup_dir, '**', 'firmware'), recursive=True)[0]
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
    parser.add_argument('--config',
                        help='path to configuration file')
    parser.add_argument('--mac',
                        help='override MAC address')

    # parse command line arguments
    args = parser.parse_args(sys.argv[1:])

    try:
        main(args)
    except SSHError as e:
        print(str(e))
        sys.exit(1)
    except RestoreStop:
        sys.exit(2)
