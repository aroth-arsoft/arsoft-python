#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile
import logging

class xmpp_config(object):

    def __init__(self, filename=None, sender=None, password=None, recipient=None, ipv4=False, ipv6=False, loglevel='ERROR'):
        self.sender = sender
        self.password = password
        self.recipient = recipient
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.loglevel = loglevel
        if filename is not None:
            self.open(filename)

    def open(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.open(filename)

        self.sender = inifile.get(None, 'From', '') 
        self.recipient = inifile.get(None, 'To', '') 
        self.password = inifile.get(None, 'Password', '') 
        self.ipv4 = inifile.getAsBoolean(None, 'IPv4', False)
        self.ipv6 = inifile.getAsBoolean(None, 'IPv6', False)
        self.loglevel = inifile.get(None, 'LogLevel', 'ERROR')
        return True

    def save(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.open(filename)

        inifile.set(None, 'From', self.sender) 
        inifile.set(None, 'To', self.recipient) 
        inifile.set(None, 'Password', self.password) 
        inifile.setAsBoolean(None, 'IPv4', self.ipv4)
        inifile.setAsBoolean(None, 'IPv6', self.ipv6)
        inifile.set(None, 'LogLevel', self.loglevel) 
        return inifile.save(filename)
    
    def __str__(self):
        ret = ''
        ret = ret + 'sender=' + str(self.sender) + ','
        ret = ret + 'password=' + str(self.password) + ','
        ret = ret + 'recipient=' + str(self.recipient) + ','
        ret = ret + 'ipv4=' + str(self.ipv4) + ','
        ret = ret + 'ipv6=' + str(self.ipv6) + ','
        ret = ret + 'loglevel=' + str(self.loglevel)
        return ret

    @property
    def loglevel_numeric(self):
        numeric_level = getattr(logging, self.loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % self.loglevel)
        return numeric_level
