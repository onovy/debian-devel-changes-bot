# -*- coding: utf-8 -*-
#
#   Debian Changes Bot
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

import threading

from cStringIO import StringIO
from pydbus import SystemBus
from gi.repository import GLib


class BTSDBusService(object):
    """
        <node>
            <interface name='org.debian.BTS'>
                <method name='Inject'>
                    <arg type='s' name='mail' direction='in' />
                    <arg type='i' name='response' direction='out' />
                </method>
                <method name='Quit' />
            </interface>
        </node>
    """

    interface_name = "org.debian.BTS"
    object_path = "/org/debian/BTS"

    def __init__(self, callback):
        self.quit = False
        self.callback = callback
        self.cv = threading.Condition()
        self.thread = None
        self.messages = []
        self.max_messages = 10

    def start(self):
        self.quit = False
        self.thread = threading.Thread(target=self.process_mails)
        self.thread.start()

    def process_mails(self):
        while not self.quit:
            with self.cv:
                while not self.quit and len(self.messages) == 0:
                    self.cv.wait()

                if self.quit:
                    self.thread = None
                    return

                mail = self.messages[0]
                self.messages = self.messages[1:]

            mail = mail.decode('base64')
            self.callback(StringIO(mail))

        self.thread = None

    @property
    def is_running(self):
        return self.thread is not None and not self.quit


    def Inject(self, mail):
        if self.quit:
            return 1

        with self.cv:
            if len(self.messages) >= self.max_messages:
                return 2

            self.messages.append(mail)
            self.cv.notify()

        return 0

    def Quit(self):
        with self.cv:
            self.quit = True
            self.cv.notify()

    stop = Quit


def inject(mail, bus=None):
    if bus is None:
        bus = SystemBus()

    mail = mail.encode('base64')
    try:
        bts = bus.get(BTSDBusService.interface_name)
        return bts.Inject(mail)
    except GLib.Error:
        return -1


def quit(bus=None):
    if bus is None:
        bus = SystemBus()

    try:
        bts = bus.get(BTSDBusService.interface_name)
        bts.Quit()
    except GLib.Error:
        return -1

