#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

import sys
import os
from arsoft.inifile import *
from . import config

class CCDFile(object):
    def __init__(self, filename=None, configfile=None):
        self._conf = None
        self.last_error = None
        self._name = None
        self._ostype = None
        self._mailnotify = None
        self._disable_private_key_encryption = None
        self._auth_user_pass_file = None
        self._configfile = configfile
        self._certfile = None
        self._keyfile = None
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
            if self.filename:
                self._name = os.path.basename(self.filename)
            for comment in self._conf.comments:
                if comment.startswith('name'):
                    (dummy, self._name) = comment.split(' ', 1)
                    break
            return self._name

    @property
    def certfile(self):
        if self._certfile:
            return self._certfile
        else:
            for comment in self._conf.comments:
                if comment.startswith('certfile'):
                    (dummy, self._certfile) = comment.split(' ', 1)
                    break
            return self._certfile

    @property
    def keyfile(self):
        if self._keyfile:
            return self._keyfile
        else:
            for comment in self._conf.comments:
                if comment.startswith('keyfile'):
                    (dummy, self._keyfile) = comment.split(' ', 1)
                    break
            return self._keyfile

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
    def mailnotify(self):
        if self._mailnotify:
            return self._mailnotify
        else:
            for comment in self._conf.comments:
                if comment.startswith('mailnotify'):
                    (dummy, self._mailnotify) = comment.split(' ', 1)
                    break
            return self._mailnotify

    @property
    def disable_private_key_encryption(self):
        if self._disable_private_key_encryption:
            return self._disable_private_key_encryption
        else:
            self._disable_private_key_encryption = False
            for comment in self._conf.comments:
                if comment.startswith('disable-private-key-encryption'):
                    self._disable_private_key_encryption = True
                    break
            return self._disable_private_key_encryption

    @property
    def auth_user_pass_file(self):
        if self._auth_user_pass_file:
            return self._auth_user_pass_file
        else:
            for comment in self._conf.comments:
                if comment.startswith('auth-user-pass-file'):
                    (dummy, self._auth_user_pass_file) = comment.split(' ', 1)
                    break
            return self._auth_user_pass_file

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
