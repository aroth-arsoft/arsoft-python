#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from utils import platform_is_windows

import os
import sys
import socket

if platform_is_windows:
    DEFAULT_HOSTS_FILE = 'windows/system32/etc/hosts'
    DEFAULT_HOSTNAME_FILE = None
else:
    DEFAULT_HOSTS_FILE = '/etc/hosts'
    DEFAULT_HOSTNAME_FILE = '/etc/hostname'
    
class HostnameFile(object):
    def __init__(self, filename=DEFAULT_HOSTNAME_FILE):
        self.filename = filename
        self.hostname = None
        self.last_error = None
        if filename is not None:
            self.open(filename)

    @property
    def name(self):
        return self.filename

    def open(self, filename=None):
        if filename is None:
            filename = self.filename
        self.hostname = None
        ret = False
        try:
            with open(filename, 'r') as f:
                line = f.readline()
                self.hostname = line.strip()
                ret = True
        except IOError as e:
            self.last_error = e
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        ret = False
        try:
            with open(filename, 'w') as f:
                if self.hostname:
                    f.write(str(self.hostname) + '\n')
                f.close()
                ret = True
        except IOError as e:
            self.last_error = e
        return ret

class HostsFile(object):
    def __init__(self, filename=DEFAULT_HOSTS_FILE):
        self.filename = filename
        self._content = []
        self.valid = False
        self.last_error = None
        if filename is not None:
            self.valid = self.open(filename)

    @property
    def name(self):
        return self.filename

    class HostLine(object):
        def __init__(self, raw_line=None):
            self._address = None
            self._hostnames = []
            self._comment = None
            self._original = raw_line

            if raw_line:
                self.parse(raw_line)

        def parse(self, raw_line):
            self._address = None
            idx = raw_line.find('#')
            if idx >= 0:
                self._comment = raw_line[idx + 1:].strip()
                split_line = [s.strip() for s in raw_line[0:idx].split()]
            else:
                self._comment = None
                split_line = [s.strip() for s in raw_line.split()]

            self._hostnames = []
            i = 0
            num_elems = len(split_line)
            while i < num_elems:
                if self._address is None:
                    self._address = split_line[i]
                else:
                    self._hostnames.append(split_line[i])
                i+=1

        @property
        def address(self):
            return self._address

        @address.setter
        def address(self,value):
            self._address = value
            self._original = None

        @property
        def hostnames(self):
            return self._hostnames

        @hostnames.setter
        def hostnames(self,value):
            self._hostnames = value
            self._original = None

        @property
        def comment(self):
            return self._comment

        @comment.setter
        def comment(self,value):
            self._comment = value
            self._original = None

        @property
        def has_data(self):
            if self.address is not None and len(self.hostnames) > 0:
                ret = True
            else:
                ret = False
            return ret

        def __str__(self):
            if self._original is not None:
                return self._original
            else:
                ret = ''
                if self._address is not None and len(self._hostnames) > 0:
                    ret = self._address + '\t' + ' '.join(self._hostnames)
                    if self._comment:
                        ret = ret + ' #' + self._comment
                elif self._comment:
                    ret = '#' + self._comment
                ret += '\n'
            return ret
    
    def open(self, filename=None):
        if filename is None:
            filename = self.filename
        self._content = []
        ret = False
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line_stripped = line.strip()
                    self._content.append(self.HostLine(line))
                f.close()
                ret = True
        except IOError as e:
            self.last_error = e
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        ret = False
        try:
            with open(filename, 'w') as f:
                for line in self._content:
                    f.write(str(line))
                f.close()
                ret = True
        except IOError as e:
            self.last_error = e
        return ret

    @property
    def hosts(self):
        ret = {}
        for line in self._content:
            if line.has_data:
                ret[line.address] = line.hostnames
        return ret
    
    def __str__(self):
        ret = ''
        for line in self._content:
            ret = ret + str(line)
        return ret

    def __getitem__(self, key):
        for line in self._content:
            if line.has_data:
                if line.address == key:
                    return line.hostnames
        return None

    def __setitem__(self, key, value):
        found = False
        for line in self._content:
            if line.has_data:
                if line.address == key:
                    found = True
                    if value is None:
                        del line
                    elif type(value) == str:
                        line.hostnames = [value]
                    else:
                        line.hostnames = value
                    break
        if not found:
            new_line = self.HostLine()
            new_line.address = key
            if value is None:
                new_line = None
            elif type(value) == str:
                new_line.hostnames = [value]
            else:
                new_line.hostnames = value
            if new_line:
                self._content.append(new_line)
                
    def __iter__(self):
        return self.hosts.iteritems()

if __name__ == "__main__":
    hosts = HostsFile()
    print(hosts)
    print(hosts.hosts)
    hosts['blubb'] = '12.1.1.1'
    hosts['127.0.0.1'] = '10.1.1.1'
    print(hosts.hosts)
    hosts.save('/tmp/hosts')

