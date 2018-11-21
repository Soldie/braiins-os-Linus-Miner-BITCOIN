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

MODE_SD = 'sd'
MODE_NAND = 'nand'
MODE_RECOVERY = 'recovery'

RECOVERY_MTDPARTS = 'recovery_mtdparts='


def mtdpart_size_to_int(value):
    multiplier = {
        'k': 1024,
        'm': 1024 * 1024,
        'g': 1024 * 1024 * 1024
    }.get(value[-1], None)
    return multiplier * int(value[:-1]) if multiplier else int(value)


def mtdparts_size_to_str(value):
    for unit in ['', 'k', 'm']:
        if (value % 1024) != 0:
            break
        value = int(value / 1024)
    else:
        unit = 'g'
    return '{}{}'.format(value, unit)


def parse_mtdparts(value):
    value = value[len(RECOVERY_MTDPARTS):].strip()
    start = value.index(':') + 1
    mtd_index = 0
    for mtdpart in value[start:].split(','):
        start = mtdpart.index('(')
        yield 'mtd{}'.format(mtd_index), mtdpart_size_to_int(mtdpart[:start]), mtdpart[start + 1:-1]
        mtd_index += 1


def parse_uenv(backup_dir):
    uenv_path = os.path.join(backup_dir, 'uEnv.txt')
    with open(uenv_path, 'r') as uenv_file:
        for line in uenv_file:
            if line.startswith(RECOVERY_MTDPARTS):
                return line[len(RECOVERY_MTDPARTS):].strip()
    return None


def get_output_dir(path, mac):
    output_dir = os.path.join(path, '{}-{:%Y-%m-%d}'.format(mac.replace(':', ''), datetime.datetime.now()))
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def ssh_mode(ssh):
    stdout, _ = ssh.run('cat', '/etc/bos_mode')
    return next(stdout).strip()


def ssh_mac(ssh):
    stdout, _ = ssh.run('cat', '/sys/class/net/eth0/address')
    return next(stdout).strip()


def ssh_backup(args, ssh, path, mac):
    print('Backuping miner NAND...')
    mtdparts = []
    with ssh.pipe('cat', '/proc/mtd') as remote:
        next(remote.stdout)
        for line in remote.stdout:
            dev, size, _, name = line.split()
            dev = dev[:-1]
            size = int(size, 16)
            name = name[1:-1]
            if not args.no_nand_backup:
                print('Backup {} ({})'.format(dev, name))
                dump_path = os.path.join(path, dev + '.bin')
                with open(dump_path, "wb") as local_dump, ssh.pipe('/usr/sbin/nanddump', '/dev/' + dev) as remote_dump:
                    shutil.copyfileobj(remote_dump.stdout, local_dump)
            mtdparts.append('{}({})'.format(mtdparts_size_to_str(size), name))

    with open(os.path.join(path, 'uEnv.txt'), 'w') as uenv:
        uenv.write('recovery=yes\n'
                   'recovery_mtdparts=mtdparts=pl35x-nand:{}\n'
                   'ethaddr={}\n'.format(','.join(mtdparts), mac))
    return True


def ssh_restore(args, ssh, backup_dir, mtdparts):
    for dev, size, name in mtdparts:
        print('Restore {} ({})'.format(dev, name))
        dump_path = os.path.join(backup_dir, dev + '.bin')
        with open(dump_path, "rb") as local_dump, ssh.pipe('mtd', '-e', name, 'write', '-', name) as remote_dump:
            shutil.copyfileobj(local_dump, remote_dump.stdin)
    ssh_restore_reboot(args, ssh)


def ssh_restore_reboot(args, ssh):
    print('Restore finished successfully!')
    if args.mode == MODE_SD:
        print('Halting system...')
        print('Please turn off the miner and change jumper to boot it from NAND!')
        ssh.run('/sbin/halt')
    else:
        print('Rebooting to restored firmware...')
        ssh.run('/sbin/reboot')
