#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os

class Config(object):

    def __init__(self, configdir='/etc/openvpn', extension='.conf'):
        self._config_directory = configdir
        self._config_extension = extension
        self._refresh_names()
        
    def _refresh_names(self):
        self._names = []
        if os.path.isdir(self._config_directory):
            for filename in os.listdir(self._config_directory):
                (basename, ext) = os.path.splitext(filename)
                if ext == self._config_extension:
                    self._names.append(basename)

    def __str__(self):
        ret = "config directory: " + str(self._config_directory) + "\r\n" +\
            "config extension: " + str(self._config_extension) + "\r\n"
        if len(self._names) > 0:
            ret = ret + "configs:\r\n"
            for name in self._names:
                ret = ret + "  " + name + "\r\n"
        else:
            ret = ret + "configs: <none>\r\n"
        return ret

if __name__ == '__main__':
    c = Config()

    print(c)
