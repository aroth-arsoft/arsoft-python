#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

import sys
import os
from arsoft.inifile import *
from arsoft.crypto import CertificateFile
from arsoft.utils import replace_invalid_chars
import config

class ConfigFile(object):
    def __init__(self, filename=None, config_name=None, zipfile=None):
        self._conf = None
        self.last_error = None
        self._name = None
        self._zipfile = zipfile

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
                self._name = config_name
            else:
                self.filename = filename

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
                ret = False
            else:
                ret = True
        return ret
    
    def save(self, filename=None):
        if filename is None:
            filename = self.fileobject if self.fileobject else self.filename
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
    def is_config_file(filename):
        conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if conf.open(filename):
            # must have either a remote or a server line
            remote = conf.get(section=None, key='remote', default=None)
            server = conf.get(section=None, key='server', default=None)

            ret = True if remote or server else False
        else:
            ret = False
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
                if self.config._zipfile is None:
                    self._fp = open(self.filename, 'r')
                else:
                    self._fp = self.config._zipfile[self.filename]
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
            
        def copyTo(self, target_directory):
            self._open()
            if self._fp:
                target_fullname = os.path(target_directory, self.filename)
                try:
                    target_fp = open(target_fullname, 'w')
                    shutil.copyfileobj(self._fp, target_fp)
                    target_fp.close()
                    ret = True
                except IOError as e:
                    self.last_error = e
                    ret = False
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
    def suggested_private_directory(self):
        name = self.name
        if name:
            at_char = name.find('@')
            if at_char > 0:
                name = name[0:at_char]
            ret = replace_invalid_chars(name)
        else:
            ret = None
        return ret

    @property
    def suggested_filename(self):
        name = self.name
        if name:
            at_char = name.find('@')
            if at_char > 0:
                name = name[0:at_char]
            ret = replace_invalid_chars(name) + '.conf'
        else:
            ret = None
        return ret

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
    def cert_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='cert', default=None)
        else:
            ret = None
        return ret

    @cert_filename.setter
    def cert_filename(self, value):
        print('cert_filename.setter %s' %value)
        if self._conf is not None:
            ret = self._conf.set(section=None, key='cert', value=value)

    @property
    def cert_file(self):
        f = self.cert_filename
        if f is not None:
            ret = CertificateFile(self.NestedFile(self, f)) if f else None
        else:
            ret = None
        return ret

    @property
    def key_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='key', default=None)
        else:
            ret = None
        return ret

    @property
    def key_file(self):
        f = self.key_filename
        if f is not None:
            ret = self.NestedFile(self, f) if f else None
        else:
            ret = None
        return ret

    @property
    def ca_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='ca', default=None)
        else:
            ret = None
        return ret

    @property
    def ca_file(self):
        f = self.ca_filename
        if f is not None:
            ret = CertificateFile(self.NestedFile(self, f)) if f else None
        else:
            ret = None
        return ret

    @property
    def dh_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='dh', default=None)
        else:
            ret = None
        return ret

    @property
    def dh_file(self):
        f = self.dh_filename
        if f is not None:
            ret = self.NestedFile(self, f) if f else None
        else:
            ret = None
        return ret

    @property
    def crl_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='crl', default=None)
        else:
            ret = None
        return ret

    @property
    def crl_file(self):
        f = self.crl_filename
        if f is not None:
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
