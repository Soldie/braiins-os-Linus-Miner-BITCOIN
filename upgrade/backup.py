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

import datetime
import shutil
import os


def mtdparts_size(value):
    for unit in ['', 'k', 'm']:
        if (value % 1024) != 0:
            break
        value = int(value / 1024)
    else:
        unit = 'g'
    return '{}{}'.format(value, unit)


def ssh_backup(ssh, path):
    print('Processing miner backup...')
    with ssh.pipe('cat', '/sys/class/net/eth0/address') as remote:
        mac = next(remote.stdout).strip()
    backup_dir = os.path.join(path, '{}-{:%Y-%m-%d}'.format(mac.replace(':', ''), datetime.datetime.now()))
    os.makedirs(backup_dir, exist_ok=True)
    mtdparts = []
    with ssh.pipe('cat', '/proc/mtd') as remote:
        next(remote.stdout)
        for line in remote.stdout:
            dev, size, _, name = line.split()
            dev = dev[:-1]
            size = int(size, 16)
            name = name[1:-1]
            print('Backup {} ({})'.format(dev, name))
            dump_path = os.path.join(backup_dir, dev + '.bin')
            with open(dump_path, "wb") as local_dump, ssh.pipe('/usr/sbin/nanddump', '/dev/' + dev) as remote_dump:
                shutil.copyfileobj(remote_dump.stdout, local_dump)
            mtdparts.append('{}({})'.format(mtdparts_size(size), name))

    with open(os.path.join(backup_dir, 'uEnv.txt'), 'w') as uenv:
        uenv.write('recovery=yes\n'
                   'recovery_mtdparts=mtdparts=pl35x-nand:{}\n'
                   'ethaddr={}\n'.format(','.join(mtdparts), mac))
    return True
