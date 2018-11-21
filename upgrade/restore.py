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
import sys
import os

import upgrade.platform as platform
import upgrade.backup as backup

from upgrade.platform import PlatformStop
from upgrade.ssh import SSHManager, SSHError
from upgrade.transfer import wait_for_port
from tempfile import TemporaryDirectory
from glob import glob

USERNAME = 'root'
PASSWORD = None

REBOOT_DELAY = (3, 8)


class RestoreStop(Exception):
    pass


def restore_from_dir(args, backup_dir):
    mtdparts_params = backup.parse_uenv(backup_dir)
    mtdparts = list(backup.parse_mtdparts(mtdparts_params))

    host_keys = True
    while True:
        print('Connecting to remote host...')
        with SSHManager(args.hostname, USERNAME, PASSWORD, load_host_keys=host_keys) as ssh:
            args.mode = backup.ssh_mode(ssh)
            print('Detected bOS mode: {}'.format(args.mode))
            if args.mode == backup.MODE_NAND:
                # restart miner to recovery mode with target MTD parts
                ssh.run('fw_setenv', backup.RECOVERY_MTDPARTS[:-1], '"{}"'.format(mtdparts_params))
                ssh.run('miner', 'run_recovery')
                # do not use host keys after restart because recovery mode has different keys for the same MAC
                host_keys = False
            else:
                # restore firmware from SD or recovery mode
                platform.restore_firmware(args, ssh, backup_dir, mtdparts)
                break
        # continue after miner is in the recovery mode
        print('Rebooting...', end='')
        wait_for_port(args.hostname, 22, REBOOT_DELAY)


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
