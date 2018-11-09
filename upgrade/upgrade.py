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
import sys

import upgrade.hwid as hwid
import upgrade.platform as platform
import upgrade.backup as backup

from upgrade.platform import PlatformStop
from upgrade.ssh import SSHManager, SSHError
from upgrade.transfer import upload_local_files

USERNAME = 'root'
PASSWORD = None

SYSTEM_DIR = 'system'
BACKUP_DIR = 'backup'
SOURCE_DIR = 'firmware'
TARGET_DIR = '/tmp/firmware'


class UpgradeStop(Exception):
    pass


def check_compatibility(ssh):
    try:
        with ssh.open('/tmp/sysinfo/board_name', 'r') as remote_file:
            board_name = next(remote_file).strip()
            print("This script cannot be used for remote target with board name '{}'!".format(board_name))
            if board_name in ('dm1-g9', 'dm1-g19', 'am1-s9'):
                print("Remote target is running braiins OS already and should be upgraded as follows:")
                print("- from standard web interface")
                print("- from command line with 'opkg' utility")
            raise UpgradeStop
    except subprocess.CalledProcessError:
        pass


def main(args):
    print("Connecting to remote host...")
    with SSHManager(args.hostname, USERNAME, PASSWORD) as ssh:
        # check compatibility of remote server
        check_compatibility(ssh)

        if not args.no_backup:
            mac = backup.ssh_mac(ssh)
            backup_dir = backup.get_output_dir(BACKUP_DIR, mac)
            if not platform.backup_firmware(args, ssh, backup_dir, mac):
                raise UpgradeStop

        # prepare target directory
        ssh.run('rm', '-fr', TARGET_DIR)
        ssh.run('mkdir', '-p', TARGET_DIR)

        # upgrade remote system with missing utilities
        if not platform.prepare_system(ssh, SYSTEM_DIR):
            raise UpgradeStop

        # copy firmware files to the server over SFTP
        sftp = ssh.open_sftp()
        sftp.chdir(TARGET_DIR)
        print("Uploading firmware...")
        upload_local_files(sftp, SOURCE_DIR)
        sftp.close()

        # generate HW identifier for miner
        hw_id = hwid.generate()

        # run stage1 upgrade process
        try:
            print("Upgrading firmware...")
            stdout, _ = ssh.run('cd', TARGET_DIR, '&&', 'ls', '-l', '&&',
                                "/bin/sh stage1.sh '{}'".format(hw_id))
        except subprocess.CalledProcessError as error:
            for line in error.stderr.readlines():
                print(line, end='')
        else:
            for line in stdout.readlines():
                print(line, end='')
            print('Upgrade was successful!')
            print('Rebooting...')
            try:
                ssh.run('/sbin/reboot')
            except subprocess.CalledProcessError:
                # reboot returns exit status -1
                pass


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('hostname',
                        help='hostname of miner with original firmware')
    parser.add_argument('--no-backup', action='store_true',
                        help='skip NAND backup before upgrade')

    # parse command line arguments
    args = parser.parse_args(sys.argv[1:])

    try:
        main(args)
    except SSHError as e:
        print(str(e))
        sys.exit(1)
    except UpgradeStop:
        sys.exit(2)
    except PlatformStop:
        sys.exit(3)
