#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

from arsoft.inifile import *
import sys
import os
import config

class ConfigFile:
    def __init__(self, filename=None, config_name=None):
        self._conf = None

        if filename is None and config_name is not None:
            cfg = config.Config()
            self.filename = cfg.get_config_file(config_name)
        else:
            self.filename = filename
            
        self._parse_file()

    def _parse_file(self):
        self._conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        print('check ' + self.filename)
        if not self._conf .open(self.filename):
            self._conf = None
            ret = False
        else:
            ret = True
        return ret
        
    @property
    def client(self):
        remote = self._conf.get(section=None, key='remote', default=None)
        return True if remote is not None else False

    @property
    def server(self):
        server = self._conf.get(section=None, key='server', default=None)
        return True if server is not None else False

    @property
    def status_version(self):
        if self._conf is not None:
            ret = int(self._conf.get(section=None, key='status-version', default=-1))
        else:
            ret = None
        return ret

    @property
    def status_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            fe = f.split(' ')
            ret = fe[0]
        else:
            ret = None
        return ret

    @property
    def status_interval(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            fe = f.split(' ')
            if len(fe) > 1:
                ret = int(fe[1])
            else:
                ret = -1
        else:
            ret = None
        return ret

    def __str__(self):
        ret = "config file " + str(self.filename) + "\r\n" +\
            "status file: " + str(self.status_file) + "\r\n" +\
            "status version: " + str(self.status_version) + "\r\n" +\
            "status interval: " + str(self.status_interval) + "\r\n" +\
            "client: " + str(self.client) + "\r\n" +\
            "server: " + str(self.server) + "\r\n" +\
            ""
        return ret

if __name__ == '__main__':
    files = sys.argv[1:]

    for file in files:
        if os.path.isfile(file):
            f = ConfigFile(filename=file)
        else:
            f = ConfigFile(config_name=file)
        print(f)
