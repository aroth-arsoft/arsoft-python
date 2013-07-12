#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

import sys
import os
from arsoft.inifile import *
import config

class CCDFile(object):
    def __init__(self, filename=None, configfile=None):
        self._conf = None
        self.last_error = None
        self._name = None
        self._ostype = None
        self._configfile = configfile
        self.filename = filename
        self._parse_file()

    def _parse_file(self):
        self._conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if not self._conf.open(self.filename):
            self.last_error = self._conf.last_error
            self._conf = None
            ret = False
        else:
            ret = True
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        if self._conf:
            if not self._conf.save(filename):
                ret = False
                self.last_error = self._conf.last_error
            else:
                ret = True
        else:
            ret = False
        return ret

    @staticmethod
    def is_ccdfile(filename):
        conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if conf.open(filename):
            ret = True
        else:
            ret = False
        return ret

    @property
    def name(self):
        if self._name:
            return self._name
        else:
            for comment in self._conf.comments:
                if comment.startswith('name'):
                    (dummy, self._name) = comment.split(' ', 1)
                    break
            return self._name

    @property
    def ostype(self):
        if self._ostype:
            return self._ostype
        else:
            for comment in self._conf.comments:
                if comment.startswith('ostype'):
                    (dummy, self._ostype) = comment.split(' ', 1)
                    break
            return self._ostype

    @property
    def routes(self):
        if self._conf:
            ret = []
            iroute = self._conf.getAsArray(section=None, key='iroute', default=[])
            for r in iroute:
                (network, netmask) = r.split(' ', 1)
                ret.append( (network, netmask) )
        else:
            ret = None
        return ret

    @property
    def push_options(self):
        if self._conf:
            ret = []
            opts = self._conf.getAsArray(section=None, key='push', default=[])
            for r in opts:
                r = unquote_string(r)
                idx = r.find(' ')
                if idx > 0:
                    option = r[0:idx].strip()
                    value = r[idx+1:]
                else:
                    option = r.strip()
                    value = None
                ret.append( (option, value) )
        else:
            ret = None
        return ret

    @property
    def valid(self):
        return True if self._conf is not None else False

    def __str__(self):
        ret = "file " + str(self.filename) + "\r\n" +\
            ""
        return ret

if __name__ == '__main__':
    files = sys.argv[1:]

    for file in files:
        f = CCDFile(filename=file)
        print(f)
