# -*- coding: utf-8 -*-
#
#   Debian Changes Bot
#   Copyright (C) 2008 Chris Lamb <chris@chris-lamb.co.uk>
#   Copyright (C) 2016 Sebastian Ramacher <sramacher@debian.org>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import threading

from DebianDevelChangesBot import NewDataSource


class RmQueue(NewDataSource):
    MATCHER = re.compile(r'<div class="subject">([^:]+): ')
    URL = 'https://ftp-master.debian.org/removals.html'
    INTERVAL = 60 * 30

    packages = set()
    lock = threading.Lock()

    def update(self):
        response = self.session.get(self.URL)
        response.raise_for_status()

        data = response.text
        packages = self.MATCHER.findall(data)

        with self.lock:
            self.packages = packages

    def get_size(self):
        with self.lock:
            size = len(self.packages)
            if size > 0:
                return size
            return None

    def is_rm(self, pkg):
        with self.lock:
            return pkg in self.packages
