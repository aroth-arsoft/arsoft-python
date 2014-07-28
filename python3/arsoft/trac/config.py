#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import os
from arsoft.inifile import IniFile

class TracConfig(object):
    def __init__(self, tracenv=None, config_file=None, verbose=False):
        if config_file is not None:
            self._config_file = config_file
        elif tracenv is not None:
            self._config_file = os.path.join(tracenv, 'conf/trac.ini')
        else:
            self._config_file = None
        self._verbose = verbose
        self._inifile = None

    def open(self, tracenv=None, config_file=None):
        if config_file is not None:
            self._config_file = config_file
        elif tracenv is not None:
            self._config_file = os.path.join(tracenv, 'conf/trac.ini')
        self._inifile = IniFile(None, commentPrefix=';', keyValueSeperator='=', disabled_values=False)
        return self._inifile.open(self._config_file)

    @property
    def enabled_components(self):
        ret = [] 
        components_section = self._inifile.section('components')
        if components_section is not None:
            for k, v in components_section.get_all():
                if v == 'enabled':
                    ret.append(k)
        return ret

if __name__ == '__main__':
    t = TracConfig(tracenv=sys.argv[1])
    t.open()
    print((t.enabled_components))
 
