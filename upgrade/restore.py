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
import time
import sys
import os

import upgrade.platform as platform
import upgrade.backup as backup

from upgrade.platform import PlatformStop
from upgrade.ssh import SSHManager, SSHError
from upgrade.transfer import wait_net_service
from tempfile import TemporaryDirectory
from glob import glob

USERNAME = 'root'
PASSWORD = None

REBOOT_DELAY = (3, 8)


class RestoreStop(Exception):
    pass


def wait(delay):
    for _ in range(delay):
        time.sleep(1)
        print('.', end='')
        sys.stdout.flush()


def wait_for_reboot(hostname, delay):
    print('Rebooting...', end='')
    delay_before, delay_after = delay
    wait(delay_before)
    while not wait_net_service(hostname, 22, 1):
        print('.', end='')
        sys.stdout.flush()
    wait(delay_after)
    print()


def restore_from_dir(args, backup_dir):
    mtdparts_params = backup.parse_uenv(backup_dir)
    mtdparts = list(backup.parse_mtdparts(mtdparts_params))

    if not args.sd_recovery:
        print("Connecting to remote host...")
        try:
            with SSHManager(args.hostname, USERNAME, PASSWORD) as ssh:
                ssh.run('fw_setenv', backup.RECOVERY_MTDPARTS[:-1], '"{}"'.format(mtdparts_params))
                ssh.run('miner', 'run_recovery')
            wait_for_reboot(args.hostname, REBOOT_DELAY)
        except SSHError as e:
            print(str(e))
            return

    print("Connecting to remote host...")
    # do not use host keys because recovery mode has different keys for the same MAC
    with SSHManager(args.hostname, USERNAME, PASSWORD, load_host_keys=False) as ssh:
        platform.restore_firmware(args, ssh, backup_dir, mtdparts)


def restore_firmware(args, backup_dir):
    with platform.prepare_restore(args):
        restore_from_dir(args, backup_dir)


def main(args):
    if os.path.isdir(args.backup):
        restore_firmware(args, args.backup)
    else:
        with TemporaryDirectory() as backup_dir:
            tar = tarfile.open(args.backup)
            print('Extracting backup tarball...')
            tar.extractall(path=backup_dir)
            tar.close()
            uenv_path = glob(os.path.join(backup_dir, '*', 'uEnv.txt'))
            if not uenv_path:
                print('Invalid backup tarball!')
                return
            backup_dir = os.path.split(uenv_path[0])[0]
            restore_firmware(args, backup_dir)


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('backup',
                        help='path to directory or tgz file with data for miner restore')
    parser.add_argument('hostname',
                        help='hostname of miner with bOS firmware')
    parser.add_argument('--sd-recovery', action='store_true',
                        help='use SD card recovery image with generated uEnv.txt')

    platform.add_restore_arguments(parser)

    # parse command line arguments
    args = parser.parse_args(sys.argv[1:])

    try:
        main(args)
    except SSHError as e:
        print(str(e))
        sys.exit(1)
    except RestoreStop:
        sys.exit(2)
    except PlatformStop:
        sys.exit(3)
