#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import socket
import select
import sys

class ManagementInterface(object):
    MGMT_HEADER = 'OpenVPN Management Interface Version'
    def __init__(self, socket_addr=None, timeout=5):
        self._socket_addr = socket_addr
        self._socket = None
        self._timeout = timeout
        self._header = None
        
    def open(self, socket_addr=None):
        if socket_addr is None:
            socket_addr = self._socket_addr
        if socket_addr[0] == '/' or socket_addr.startswith('unix:'):
            if socket_addr.startswith('unix:'):
                socket_addr = socket_addr[5:]
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(socket_addr)
            except socket.error:
                sock = None
        else:
            if ':' in socket_addr:
                (hostname, port) = socket_addr.split(socket_addr)
            else:
                hostname = socket_addr
                port = 23
            sock = socket.create_connection((hostname, port), self._timeout)

        if sock:
            self._socket = sock
            self._socket.setblocking(0)
            self._socket.sendall('\n')
            self._header = self._read_header(self._timeout)
            if self._header is not None:
                ret = True
            else:
                ret = False
        else:
            ret = False
        return ret

    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None

    def _purge(self, timeout):
        # purge any available data
        self._read_all(timeout)
        
    @property
    def version(self):
        if self._header is None:
            return None
        else:
            idx = self._header.find(ManagementInterface.MGMT_HEADER)
            if idx >= 0:
                l = len(ManagementInterface.MGMT_HEADER)
                s = self._header[idx + l + 1:idx + l + 2]
                ret = int(s)
            else:
                ret = -1
            return ret

    def _read_header(self, timeout):
        data = ''
        s_reply = ([self._socket], [], [])
        s_args = s_reply
        if timeout is not None:
            s_args = s_args + (timeout,)
            from time import time
            time_start = time()

        ret = None
        while select.select(*s_args) == s_reply:
            buf = self._socket.recv(256)
            if data is None:
                break
            else:
                data = data + buf

            if data.endswith("\r\n"):
                ret = data.split('\r\n')[0]
                break
            if timeout is not None:
                elapsed = time() - time_start
                if elapsed >= timeout:
                    break
                s_args = s_reply + (timeout-elapsed,)
        return ret

    def _read_response(self, timeout):
        data = ''
        s_reply = ([self._socket], [], [])
        s_args = s_reply
        if timeout is not None:
            s_args = s_args + (timeout,)
            from time import time
            time_start = time()

        ret = None
        while select.select(*s_args) == s_reply:
            buf = self._socket.recv(256)
            if data is None:
                break
            else:
                data = data + buf

            if data.endswith("END\r\n"):
                ret = data.split('\r\n')
                break
            if timeout is not None:
                elapsed = time() - time_start
                if elapsed >= timeout:
                    break
                s_args = s_reply + (timeout-elapsed,)
        return ret

    def _send_command(self, command):
        self._socket.sendall(command + '\n')
        return self._read_response(self._timeout)

    def status(self, version=3):
        return self._send_command('status ' + str(version))

    def state(self):
        return self._send_command('state')

if __name__ == '__main__':
    m = ManagementInterface('unix:/run/openvpn.' + sys.argv[1] + '.socket')
    if m.open():
        print((m.version))
        r = m.status()
        print (r)
        m.close()
    else:
        print(('failed to open openvpn management socket ' + sys.argv[1]))
