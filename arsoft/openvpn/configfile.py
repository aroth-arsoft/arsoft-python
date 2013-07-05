#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

import sys
import os
from arsoft.inifile import *
from arsoft.crypto import CertificateFile
import config

class ConfigFile:
    def __init__(self, filename=None, config_name=None):
        self._conf = None
        self.last_error = None
        self.name = None

        if filename:
            if hasattr(filename , 'read'):
                self.fileobject = filename
                self.filename = filename.name
            else:
                self.fileobject = None
                self.filename = filename
        else:
            self.fileobject = None
            if config_name is not None:
                cfg = config.Config()
                self.filename = cfg.get_config_file(config_name)
                self.config_directory = os.path.dirname(self.filename)
                self.name = config_name
            else:
                self.filename = filename
                if self.filename is not None:
                    bname = os.path.basename(self.filename)
                    (self.name, ext) = os.path.splitext(bname)

        self.config_directory = os.path.dirname(self.filename) if self.filename else None
        self._parse_file()

    def _parse_file(self):
        self._conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if self.fileobject is not None:
            if not self._conf.open(self.fileobject):
                self.last_error = self._conf.last_error
                self._conf = None
                ret = False
            else:
                ret = True
        else:
            if not self._conf.open(self.filename):
                self.last_error = self._conf.last_error
                self._conf = None
                self._name = None
                ret = False
            else:
                ret = True
        return ret
    
    class NestedFile(object):
        def __init__(self, config, filename):
            self.config = config
            self.filename = filename
            self._fp = None

        @property
        def abspath(self):
            return os.path.join(self.config.config_directory, self.filename)
        
        def __str__(self):
            return self.abspath
        
        def _open(self):
            if self._fp is None:
                self._fp = open(self.filename, 'r')
            return True if self._fp else False
        
        def __iter__(self):
            self._open()
            if self._fp:
                return iter(self._fp)
            else:
                raise IOError('no file object')

        def read(self, size=None):
            self._open()
            if self._fp:
                return self._fp.read(size)
            else:
                raise IOError('no file object')

        def seek(self, offset, whence=None):
            self._open()
            if self._fp:
                return self._fp.seek(offset, whence)
            else:
                raise IOError('no file object')

    @property
    def valid(self):
        return True if self._conf is not None else False

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
            if f:
                fe = f.split(' ')
                ret = os.path.join(self.config_directory, fe[0])
            else:
                ret = None
        else:
            ret = None
        return ret
    
    @property
    def cert_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='cert', default=None)
            ret = CertificateFile(self.NestedFile(self, f)) if f else None
        else:
            ret = None
        return ret

    @property
    def key_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='key', default=None)
            ret = self.NestedFile(self, f) if f else None
        else:
            ret = None
        return ret

    @property
    def ca_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='ca', default=None)
            ret = CertificateFile(self.NestedFile(self, f)) if f else None
        else:
            ret = None
        return ret

    @property
    def dh_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='dh', default=None)
            ret = self.NestedFile(self, f) if f else None
        else:
            ret = None
        return ret

    @property
    def crl_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='crl', default=None)
            ret = CertificateFile(self.NestedFile(self, f)) if f else None
        else:
            ret = None
        return ret

    @property
    def remote(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='remote', default=None)
            if f:
                fe = f.split(' ')
                ret = (fe[0], int(fe[1]))
            else:
                ret = None
        else:
            ret = None
        return ret

    @property
    def management(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='management', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) == 2:
                    ret = (fe[0], fe[1], None)
                elif len(fe) > 2:
                    ret = (fe[0], fe[1], fe[2])
                else:
                    ret = (None, None, None)
            else:
                ret = (None, None, None)
        else:
            ret = None
        return ret

    @property
    def management_socket(self):
        (mgmt_ip, mgmt_port, mgmt_pwfile) = self.management
        if mgmt_port == 'unix':
            ret = mgmt_ip
        else:
            ret = None
        return ret

    @property
    def status_interval(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) > 1:
                    ret = int(fe[1])
                else:
                    ret = -1
            else:
                ret = None
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
            "management: " + str(self.management) + "\r\n" +\
            "management_socket: " + str(self.management_socket) + "\r\n" +\
            "remote: " + str(self.remote) + "\r\n" +\
            "crl_file: " + str(self.crl_file) + "\r\n" +\
            "dh_file: " + str(self.dh_file) + "\r\n" +\
            "ca_file: " + str(self.ca_file) + "\r\n" +\
            "cert_file: " + str(self.cert_file) + "\r\n" +\
            "key_file: " + str(self.key_file) + "\r\n" +\
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
