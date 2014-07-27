#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile
from urlparse import urlparse

class slapd_defaults(object):
    def __init__(self, filename='/etc/default/slapd'):
        self._data = {}
        self._filename = filename
        self._read()

    @staticmethod
    def _unquote(value):
        value_len = len(value)
        if value[0] == '"' and value[value_len - 1] == '"':
            return value[1:value_len - 1]
        else:
            return value

    @staticmethod
    def _read_value(dict, inifile, key, default_value):
        value = inifile.get(None, key, default_value)
        value = slapd_defaults._unquote(value)
        if isinstance(default_value, list):
            value = value.split(' ')
        dict[key] = value

    def _read(self):
        self._data = {}
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        if inifile.open(self._filename):
            slapd_defaults._read_value(self._data, inifile, 'SLAPD_OPTIONS', None)
            slapd_defaults._read_value(self._data, inifile, 'SLAPD_SERVICES', [])
            slapd_defaults._read_value(self._data, inifile, 'SLAPD_USER', None)
            slapd_defaults._read_value(self._data, inifile, 'SLAPD_GROUP', None)
            ret = True
        else:
            ret = False
        return ret

    @property
    def services(self):
        return self._data['SLAPD_SERVICES']

    @property
    def public_services(self):
        ret = []
        for srv in self._data['SLAPD_SERVICES']:
            o = urlparse(srv)
            if o.scheme == 'ldapi':
                continue
            elif o.hostname == 'localhost' or o.hostname == 'loopback' or o.hostname == '127.0.0.1' or o.hostname == '::1':
                continue
            else:
                ret.append(srv)
        return ret

    def has_ldapi_service(self):
        ret = False
        for srv in self._data['SLAPD_SERVICES']:
            if srv.startswith('ldapi://'):
                ret = True
        return ret

    def has_service(self, serveruri):
        ret = False
        for srv in self._data['SLAPD_SERVICES']:
            if srv == serveruri:
                ret = True
        return ret

    def to_string(self):
        elems = []
        for (key, value) in self._data.items():
            if value is not None:
                key_value_pair = key + '="' + str(value) + '"'
                elems.append(key_value_pair)
        return ' '.join(elems)
    
    def original_string(self):
        return self._org_line

    def __str__(self):
        return self.to_string()

if __name__ == "__main__":
    s = slapd_defaults()
    print(s)
    print(s.services)
    print(s.public_services)


