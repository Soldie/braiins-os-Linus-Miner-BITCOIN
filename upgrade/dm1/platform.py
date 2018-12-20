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

from .backup import ssh_backup as backup_firmware
from .backup import ssh_restore as restore_firmware

from contextlib import contextmanager


class PlatformStop(Exception):
    pass


@contextmanager
def prepare_restore(args):
    yield


def prepare_system(ssh, path):
    pass


def cleanup_system(ssh):
    pass


def add_restore_arguments(parser):
    pass
