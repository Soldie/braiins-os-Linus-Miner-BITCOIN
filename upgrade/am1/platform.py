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

import subprocess
import time
import os

from .backup import ssh_backup


def backup_firmware(ssh, path):
    print('Preparing system for backup...')
    # before NAND dump try to stop all daemons which modify UBIFS
    # /tmp on AntMiner is mounted directly to UBIFS
    ssh.run('mount', '-t', 'tmpfs', 'tmpfs', '/tmp/')
    # stop bmminer which logs to /tmp
    ssh.run('/etc/init.d/bmminer.sh', 'stop')
    # give to system some time to kill all processes and free handles
    time.sleep(1)
    # sync everything to NAND
    ssh.run('sync')
    # start backup process
    return ssh_backup(ssh, path)


def prepare_system(ssh, path):
    binaries = [
        ('ld-musl-armhf.so.1', '/lib'),
        ('sftp-server', '/usr/lib/openssh'),
        ('fw_printenv', '/usr/sbin')
    ]

    print("Preparing remote system...")

    for file_name, remote_path in binaries:
        remote_file_name = '{}/{}'.format(remote_path, file_name)
        try:
            ssh.run('test', '!', '-e', remote_file_name)
        except subprocess.CalledProcessError:
            print("File '{}' exists on remote target already!".format(remote_file_name))
            return False

    for file_name, remote_path in binaries:
        ssh.run('mkdir', '-p', remote_path)
        remote_file_name = '{}/{}'.format(remote_path, file_name)
        print('Copy {} to {}'.format(file_name, remote_file_name))
        ssh.put(os.path.join(path, file_name), remote_file_name)
        ssh.run('chmod', '+x', remote_file_name)

    ssh.run('ln', '-fs', '/usr/sbin/fw_printenv', '/usr/sbin/fw_setenv')
    print()
    return True
