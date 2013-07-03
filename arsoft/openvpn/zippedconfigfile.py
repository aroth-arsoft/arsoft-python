#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import sys
from zipfile import ZipFile
from configfile import ConfigFile
import arsoft.utils

class ZippedConfigFile(object):

    def __init__(self, filename=None, mode='r'):
        self.filename = filename
        self.mode = mode
        self._zip = None
        self._config_file = None
        
    def _ensure_open(self):
        if self._zip is None:
            self.open()

    def open(self, filename=None, mode=None):
        if filename is None:
            filename = self.filename
        if mode is None:
            mode = self.mode

        self._zip = ZipFile(filename, mode)
        ret = True if self._zip else False
        return ret

    def close(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    @property
    def config_file(self):
        if self._config_file is None:
            self._ensure_open()
            fileinfolist = self._zip.infolist()
            for fileinfo in fileinfolist:
                (basename, ext) = os.path.splitext(fileinfo.filename)
                if ext == '.ovpn' or ext == '.conf':
                    self._config_file = fileinfo
                    break
        return self._config_file.filename if self._config_file else None

    @property
    def config_file_object(self):
        if self._config_file is None:
            self._ensure_open()
            fileinfolist = self._zip.infolist()
            for fileinfo in fileinfolist:
                (basename, ext) = os.path.splitext(fileinfo.filename)
                if ext == '.ovpn' or ext == '.conf':
                    self._config_file = fileinfo
                    break
        return self._zip.open(self._config_file.filename, self.mode) if self._config_file else None

if __name__ == '__main__':
    c = ZippedConfigFile(sys.argv[1])

    print(c)
    print(c.config_file)
    cfg = ConfigFile(c.config_file_object)
    print(cfg)
    
