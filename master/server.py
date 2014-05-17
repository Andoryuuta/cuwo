# Copyright (c) Mathias Kaerlev 2013-2014.
#
# This file is part of cuwo.
#
# cuwo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cuwo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cuwo.  If not, see <http://www.gnu.org/licenses/>.

"""
Master server that serves a single JSON file through the local filesystem
"""

import sys
sys.path += ['.', './scripts']

from cuwo import constants
from cuwo.exceptions import InvalidData
import master
import asyncio
import pygeoip
import argparse
import json
import os
import socket


WRITE_INTERVAL = 10
DEFAULT_PORT = 12364
EXPIRE_TIME = master.UPDATE_RATE * 1.5
BLACKLIST_FILE = 'blacklist.json'


class MasterServer(master.MasterProtocol):
    def __init__(self, filename, blacklist_file):
        self.filename = filename
        self.output = {}
        self.blacklist_file = blacklist_file
        self.blacklist = set()
        self.ip_database = pygeoip.GeoIP('GeoIP.dat')

        asyncio.Task(self.update())

    def datagramReceived(self, data, addr):
        host, port = addr
        if host in self.blacklist:
            return
        master.MasterProtocol.datagramReceived(self, data, addr)

    def on_bad_packet(self, addr):
        host, port = addr
        self.add_blacklist(host)

    def add_blacklist(self, host):
        self.blacklist.add(host)
        self.save_blacklist()

    def save_blacklist(self):
        with open(self.blacklist_file, 'wb') as fp:
            fp.write(json.dumps(list(self.blacklist)))

    def load_blacklist(self):
        if not os.path.isfile(self.blacklist_file):
            self.save_blacklist()  # save empty blacklist
            return
        with open(self.blacklist_file, 'rb') as fp:
            self.blacklist = set(json.loads(fp.read()))

    def update(self):
        with open(self.filename, 'wb') as fp:
            fp.write(json.dumps(list(self.output.values())))
        self.load_blacklist()
        self.output.clear()

    @asyncio.coroutine
    def resolve(self, host):
        info = yield from self.loop.getaddrinfo(host, 0)
        return info[0][4][0]

    @asyncio.coroutine
    def on_server(self, data, addr):
        host, port = addr
        data.ip = host
        if data.ip is None:
            data.ip = host
        else:
            use_ip = False
            try:
                ip = yield from self.resolve(data.ip)
                use_ip = ip == host
            except socket.gaierror:
                pass
            if not use_ip:
                data.ip = host
        self.add_server(data, host)

    def add_server(self, data, ip):
        try:
            location = self.ip_database.country_code_by_addr(ip)
        except TypeError:
            location = '?'
        data.location = location
        data.mode = data.mode or 'default'
        self.output[ip] = data.get()

    def on_packet(self, value, addr):
        host, port = addr
        if port != constants.SERVER_PORT:
            return
        try:
            asyncio.Task(self.on_server(master.ServerData(value), addr))
        except InvalidData:
            self.on_bad_packet(addr)
            return
        self.send_packet({'ack': True}, addr)


def main():
    parser = argparse.ArgumentParser(description='Run a master server')
    parser.add_argument('filename', type=str)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--blacklist', type=str,
                        default=BLACKLIST_FILE)
    args = parser.parse_args()

    port = args.port
    filename = args.filename
    blacklist_file = args.blacklist

    loop = asyncio.get_event_loop()
    protocol = MasterServer(filename, blacklist_file)

    print('Running cuwo (master) on port %s' % port.port)
    addr = (None, port)
    loop.run_until_complete(loop.create_datagram_endpoint(protocol,
                                                          local_addr=addr))

if __name__ == '__main__':
    main()
