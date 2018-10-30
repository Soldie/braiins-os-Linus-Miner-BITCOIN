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
import os

import upgrade.hwid as hwid

from upgrade.platform import backup_firmware, prepare_system
from upgrade.ssh import SSHManager, SSHError
from progress.bar import Bar

USERNAME = 'root'
PASSWORD = None

SYSTEM_DIR = 'system'
BACKUP_DIR = 'backup'
SOURCE_DIR = 'firmware'
TARGET_DIR = '/tmp/firmware'


class UpgradeStop(Exception):
    pass


class Progress:
    def __init__(self, file_path):
        self.file_path = file_path
        self.progress = None
        self._last = 0

    def __enter__(self):
        file_size = os.path.getsize(self.file_path)
        self.progress = Bar('{}:'.format(self.file_path), max=file_size)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.finish()

    def __call__(self, transferred: int, total: int):
        self.progress.next(transferred - self._last)
        self._last = transferred


def upload_files(sftp, local_path, remote_path):
    print("Uploading firmware...")
    sftp.chdir(remote_path)

    for root, dirs, files in os.walk(local_path):
        root_remote = os.path.relpath(root, local_path)
        for name in files:
            local_file = os.path.join(root, name)
            with Progress(local_file) as progress:
                sftp.put(local_file, os.path.join(root_remote, name), callback=progress)
        for name in dirs:
            sftp.mkdir(os.path.join(root_remote, name))


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

        if not args.no_backup and not backup_firmware(ssh, BACKUP_DIR):
            raise UpgradeStop

        # prepare target directory
        ssh.run('rm', '-fr', TARGET_DIR)
        ssh.run('mkdir', '-p', TARGET_DIR)

        # upgrade remote system with missing utilities
        if not prepare_system(ssh, SYSTEM_DIR):
            raise UpgradeStop

        # copy firmware files to the server over SFTP
        sftp = ssh.open_sftp()
        upload_files(sftp, SOURCE_DIR, TARGET_DIR)
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
    except UpgradeStop:
        sys.exit(1)
