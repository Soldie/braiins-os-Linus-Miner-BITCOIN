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
import tarfile
import hashlib
import shutil
import time
import os

from urllib.request import Request, urlopen
from contextlib import contextmanager
from tempfile import TemporaryFile

from .backup import ssh_backup, ssh_restore, ssh_restore_reboot
from .transfer import Progress

CONFIG_TAR = 'config.tar.gz'
XILINX_DIR = 'xilinx/'
TARGET_DIR = '/tmp/bitmain_fw'

RESTORE_DIR = 'upgrade'
RESTORE_NAME = 'restore.sh'

SUPPORTED_IMAGES = [
    '9974dd88b70cdaaa89a4dd55c25d5bc1',
    '5b07bd845685d81c092a3b0465f24ef1'
]


class PlatformStop(Exception):
    pass


def backup_firmware(args, ssh, path, mac):
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
    print('Backuping configuration files...')
    local_path = os.path.join(path, CONFIG_TAR)
    with open(local_path, 'wb') as local_file, ssh.pipe('tar', 'cvzf', '-', '/config') as remote:
        shutil.copyfileobj(remote.stdout, local_file)
    # start backup process
    return ssh_backup(args, ssh, path, mac)


def upload_bitmain_files(sftp, stream):
    # transfer original Bitmain firmware images needed for upgrade
    with tarfile.open(fileobj=stream, mode='r|*') as tarball:
        for member in tarball:
            member_file = tarball.extractfile(member)
            if not member.name.startswith(XILINX_DIR):
                if not member.isdir():
                    print("Skipping '{}'".format(member.name))
                continue
            name = member.name[len(XILINX_DIR):]
            with Progress(name, member.size) as progress:
                sftp.putfo(member_file, name, callback=progress)


def md5fo(stream):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: stream.read(4096), b''):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()


@contextmanager
def prepare_restore(args):
    url = args.factory_image
    if not url:
        # factory image is not set and standard NAND restore is used
        yield
        return

    if os.path.isfile(url):
        stream = open(url, 'rb')
    else:
        # download remote image to temporary file
        stream = TemporaryFile()
        remote = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
        print('Downloading factory image...')
        shutil.copyfileobj(remote, stream)
        stream.seek(0)

    image_md5 = md5fo(stream)
    if image_md5 not in SUPPORTED_IMAGES:
        stream.close()
        print('Unsupported factory image with MD5 digest: {}'.format(image_md5))
        raise PlatformStop

    args.factory_stream = stream
    args.factory_stream.seek(0)
    yield
    args.factory_stream.close()


def restore_bitmain_firmware(args, ssh, backup_dir, mtdparts):
    # prepare target directory
    ssh.run('rm', '-fr', TARGET_DIR)
    ssh.run('mkdir', '-p', TARGET_DIR)

    # copy firmware files to the server over SFTP
    sftp = ssh.open_sftp()
    sftp.chdir(TARGET_DIR)

    print("Uploading firmware...")
    upload_bitmain_files(sftp, args.factory_stream)

    print("Uploading restore scripts...")
    files = [
        (backup_dir, CONFIG_TAR),
        (RESTORE_DIR, RESTORE_NAME)
    ]
    for dir, file_name in files:
        local_path = os.path.join(dir, file_name)
        with Progress(local_path) as progress:
            sftp.put(local_path, file_name, callback=progress)

    sftp.close()

    # run stage1 upgrade process
    try:
        print("Restoring firmware...")
        stdout, _ = ssh.run('cd', TARGET_DIR, '&&', 'ls', '-l', '&&',
                            "/bin/sh {}".format(RESTORE_NAME))
    except subprocess.CalledProcessError as error:
        for line in error.stderr.readlines():
            print(line, end='')
        raise PlatformStop
    else:
        for line in stdout.readlines():
            print(line, end='')


def restore_firmware(args, ssh, backup_dir, mtdparts):
    if args.factory_image:
        restore_bitmain_firmware(args, ssh, backup_dir, mtdparts)
        ssh_restore_reboot(args, ssh)
    else:
        # use default NAND dump restore
        ssh_restore(args, ssh, backup_dir, mtdparts)


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


def add_restore_arguments(parser):
    parser.add_argument('--factory-image',
                        help='path/url to original firmware upgrade image')
