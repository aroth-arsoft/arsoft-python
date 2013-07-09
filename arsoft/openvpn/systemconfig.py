#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import *
import sys
import os
import config

def is_quoted_string(str):
    if len(str) > 1 and ((str[0] == '"' and str[-1] == '"') or (str[0] == '\'' and str[-1] == '\'')):
        return True
    else:
        return False

def unquote_string(str):
    if is_quoted_string(str):
        return str[1:-1]
    else:
        return str

def quote_string(str, quote_char='\''):
    return quote_char + str + quote_char

class SystemConfig(object):
    def __init__(self, filename=None, root_directory=None):
        self._conf = None
        self.open(filename, root_directory)

    @property
    def valid(self):
        return True if self._conf else False

    def open(self, filename=None, root_directory=None):
        if filename is None:
            filename = '/etc/default/openvpn'
        if root_directory is not None:
            self.filename = root_directory + filename
        else:
            self.filename = filename
        self._conf  = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        if not self._conf.open(self.filename):
            #self._conf = None
            ret = False
        else:
            ret = True

        return ret
    
    def save(self, filename=None, create_dirs=True):
        if filename is None:
            filename = self.filename
        if self._conf:
            if create_dirs:
                d = os.path.dirname(filename)
                if not os.path.isdir(d):
                    try:
                        os.makedirs(d)
                    except IOError:
                        ret = False
            ret = self._conf.save(filename)
        else:
            ret = False
        return ret

    @property
    def autostart(self):
        value = unquote_string(self._conf.get(None, 'AUTOSTART', ''))
        if value == 'none' or value == '':
            ret = set()
        else:
            ret = set(value.split(' ')) if value is not None else set()
        return ret

    @autostart.setter
    def autostart(self, value):
        if type(value) == str:
            if value == '':
                real_value = set('none')
            else:
                real_value = set(value)
        else:
            if len(value) == 0:
                real_value = set('none')
            else:
                real_value = set(value)
        self._conf.set(None, 'AUTOSTART', quote_string(' '.join(real_value)))

    @property
    def statusrefresh(self):
        value = self._conf.get(None, 'STATUSREFRESH', '10')
        ret = int(value)
        return ret

    @statusrefresh.setter
    def statusrefresh(self, value):
        self._conf.set(None, 'STATUSREFRESH', str(value))

    @property
    def optional_arguments(self):
        value = unquote_string(self._conf.get(None, 'OPTARGS', ''))
        ret = value.split(' ')
        return ret

    @optional_arguments.setter
    def optional_arguments(self, value):
        if type(value) == str:
            self._conf.set(None, 'OPTARGS', quote_string(str))
        else:
            self._conf.set(None, 'OPTARGS', quote_string(' '.join(value)))

    @property
    def omit_sendsigs(self):
        value = self._conf.get(None, 'OMIT_SENDSIGS', '0')
        ret = True if int(value) != 0 else False
        return ret

    @omit_sendsigs.setter
    def omit_sendsigs(self, value):
        self._conf.set(None, 'OMIT_SENDSIGS', '1' if int(value) != 0 else '0')
        
    def __str__(self):
        return str(self._conf)

if __name__ == '__main__':
    syscfg = SystemConfig(filename=sys.argv[1])
    print(syscfg.autostart)
    print(syscfg.optional_arguments)
    print(syscfg.statusrefresh)
    print(syscfg.omit_sendsigs)
    
    syscfg.autostart = ['None']
    print(syscfg.autostart)
    print(syscfg)
