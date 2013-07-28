#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

""" This is a parser for openvpn config files, version 3.

"""

import sys
import os
from arsoft.inifile import *
from arsoft.crypto import CertificateFile, CRLFile
from arsoft.utils import replace_invalid_chars, is_quoted_string, unquote_string, quote_string
import config
from ccdfile import CCDFile
import StringIO

class ConfigFile(object):
    def __init__(self, filename=None, config_name=None, zipfile=None):
        self._conf = None
        self.last_error = None
        self._name = None
        self._zipfile = zipfile

        if filename:
            if hasattr(filename , 'read'):
                self.fileobject = filename
                if hasattr(filename , 'name'):
                    self.filename = filename.name
                else:
                    self.filename = None
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
        self._conf = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if self.fileobject is not None:
            if not self._conf.open(self.fileobject):
                self.last_error = self._conf.last_error
                self._conf = None
                ret = False
            else:
                ret = True
        elif self.filename is not None:
            if not self._conf.open(self.filename):
                self.last_error = self._conf.last_error
                self._conf = None
                ret = False
            else:
                ret = True
        else:
            ret = False
        return ret
    
    def clone(self):
        ret = ConfigFile()
        ret._zipfile = self._zipfile
        ret._name = self._name
        ret.fileobject = self.fileobject
        ret.filename = self.filename
        ret.config_directory = self.config_directory
        ret._conf = self._conf.clone()
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
                    (dummy, name) = comment.split(' ', 1)
                    self._name = os.path.basename(name)
                    break
            return self._name

    @name.setter
    def name(self, value):
        self._name = value
        if self._conf is not None:
            for comment in self._conf.comments:
                if comment.startswith('name'):
                    self._conf.replace_comment(comment, ' name ' + str(self._name))
                    break

    @property
    def public_address(self):
        if self._conf:
            ret = self._conf.get(section=None, key='local', default=None)
            for comment in self._conf.comments:
                if comment.startswith('public-address'):
                    (dummy, ret) = comment.split(' ', 1)
                    break
        else:
            ret = None
        return ret

    @public_address.setter
    def public_address(self, value):
        if self._conf is not None:
            for comment in self._conf.comments:
                if comment.startswith('public-address'):
                    self._conf.replace_comment(comment, ' public-address ' + str(value))
                    break

    @property
    def public_port(self):
        if self._conf:
            ret = self._conf.get(section=None, key='port', default=1194)
            for comment in self._conf.comments:
                if comment.startswith('public-port'):
                    (dummy, ret) = comment.split(' ', 1)
                    break
            if ret:
                ret = int(ret)
        else:
            ret = None
        return ret

    @public_port.setter
    def public_port(self, value):
        if self._conf is not None:
            for comment in self._conf.comments:
                if comment.startswith('public-port'):
                    self._conf.replace_comment(comment, ' public-port ' + str(value))
                    break

    @property
    def ostype(self):
        if self._conf:
            ret = None
            for comment in self._conf.comments:
                if comment.startswith('ostype'):
                    (dummy, ret) = comment.split(' ', 1)
                    break
        else:
            ret = None
        return ret

    @ostype.setter
    def ostype(self, value):
        if self._conf is not None:
            for comment in self._conf.comments:
                if comment.startswith('ostype'):
                    self._conf.replace_comment(comment, ' ostype ' + str(value))
                    break

    @property
    def mailnotify(self):
        if self._conf:
            ret = None
            for comment in self._conf.comments:
                if comment.startswith('mailnotify'):
                    (dummy, ret) = comment.split(' ', 1)
                    break
        else:
            ret = None
        return ret

    @mailnotify.setter
    def mailnotify(self, value):
        if self._conf is not None:
            for comment in self._conf.comments:
                if comment.startswith('mailnotify'):
                    self._conf.replace_comment(comment, ' mailnotify ' + str(value))
                    break

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
            if self.ostype == 'win' or self.ostype == 'android' or self.ostype == 'windows':
                ret = replace_invalid_chars(name) + '.ovpn'
            else:
                ret = replace_invalid_chars(name) + '.conf'
        else:
            ret = None
        return ret

    @property
    def suggested_zip_filename(self):
        name = self.name
        if name:
            name = replace_invalid_chars(name, invalid_chars=['@'], replacement='_at_')
            ret = replace_invalid_chars(name) + '.zip'
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

    @server.setter
    def server(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='server', value=value)

    @property
    def status_version(self):
        if self._conf is not None:
            ret = int(self._conf.get(section=None, key='status-version', default=-1))
        else:
            ret = None
        return ret

    @status_version.setter
    def status_version(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='status-version', value=value)

    @property
    def suggested_status_version(self):
        return 3

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
    def suggested_status_file(self):
        name = self.name
        if name:
            at_char = name.find('@')
            if at_char > 0:
                name = name[0:at_char]
            ret = '/run/openvpn.%s.status' % replace_invalid_chars(name)
        else:
            ret = None
        return ret

    @status_file.setter
    def status_file(self, value):
        if self._conf is not None:
            interval = None
            f = self._conf.get(section=None, key='status', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) > 1:
                    interval = int(fe[1])
            if interval:
                ret = self._conf.set(section=None, key='status', value=value + ' %i' % interval)
            else:
                ret = self._conf.set(section=None, key='status', value=value)

    @property
    def status_interval(self):
        ret = None
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) > 1:
                    ret = int(fe[1])
        return ret

    @property
    def logfile(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='log', default=None)
            if f:
                ret = os.path.join(self.config_directory, f)
            else:
                ret = None
        else:
            ret = None
        return ret

    @logfile.setter
    def logfile(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='log', value=value)

    @property
    def logfile_append(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='log-append', default=None)
            if f:
                ret = os.path.join(self.config_directory, f)
            else:
                ret = None
        else:
            ret = None
        return ret

    @logfile_append.setter
    def logfile_append(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='log-append', value=value)

    @property
    def cert_filename(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='cert', default=None)
        else:
            ret = None
        return ret

    @cert_filename.setter
    def cert_filename(self, value):
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

    @key_filename.setter
    def key_filename(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='key', value=value)

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

    @ca_filename.setter
    def ca_filename(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='ca', value=value)

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

    @dh_filename.setter
    def dh_filename(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='dh', value=value)

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
            ret = self._conf.get(section=None, key='crl-verify', default=None)
        else:
            ret = None
        return ret

    @crl_filename.setter
    def crl_filename(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='crl-verify', value=value)

    @property
    def crl_file(self):
        f = self.crl_filename
        if f is not None:
            ret = CRLFile(self.NestedFile(self, f)) if f else None
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
    def local(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='local', default=None)
        else:
            ret = None
        return ret

    @property
    def protocol(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='proto', default=None)
        else:
            ret = None
        return ret

    @protocol.setter
    def protocol(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='proto', value=value)

    @property
    def cipher(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='cipher', default=None)
        else:
            ret = None
        return ret

    @cipher.setter
    def cipher(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='cipher', value=value)

    @property
    def keepalive(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='keepalive', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) >= 2:
                    ret = (int(fe[0]), int(fe[1]))
                else:
                    ret = (None, None)
            else:
                ret = (None, None)
        else:
            ret = (None, None)
        return ret

    @property
    def management(self):
        ret = (None, None, None)
        if self._conf is not None:
            f = self._conf.get(section=None, key='management', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) == 2:
                    ret = (fe[0], fe[1], None)
                elif len(fe) > 2:
                    ret = (fe[0], fe[1], fe[2])
        return ret

    @management.setter
    def management(self, value):
        if self._conf is not None:
            if isinstance(value, str):
                fe = value.split(' ')
                if len(fe) == 2:
                    value = (fe[0], fe[1], None)
                elif len(fe) > 2:
                    value = (fe[0], fe[1], fe[2])
            (addr, port, pwfile) = value
            real_value = str(addr)
            if port:
                real_value += ' %s' % (port)
                if pwfile:
                    real_value += ' %s' % (pwfile)
            ret = self._conf.set(section=None, key='management', value=real_value)

    @property
    def suggested_management(self):
        name = self.name
        if name:
            at_char = name.find('@')
            if at_char > 0:
                name = name[0:at_char]
            ret = ('/run/openvpn.%s.socket' % replace_invalid_chars(name), 'unix', None)
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

    @property
    def client_config_directory(self):
        if self._conf is not None:
            ret = self._conf.get(section=None, key='client-config-dir', default=None)
        else:
            ret = None
        return ret

    @client_config_directory.setter
    def client_config_directory(self, value):
        if self._conf is not None:
            ret = self._conf.set(section=None, key='client-config-dir', value=value)

    @property
    def client_config_files(self):
        if self.client_config_directory:
            ret = {}
            if self._zipfile:
                for ccdfilename in self._zipfile.get_files_in_directory(self.client_config_directory):
                    item = os.path.basename(ccdfilename)
                    ccdfile = CCDFile(ccdfilename, configfile=self)
                    ret[item] = ccdfile
            else:
                if self.config_directory:
                    dirname = os.path.join(self.config_directory, self.client_config_directory)
                else:
                    dirname = os.path.abspath(self.client_config_directory)
                if os.path.isdir(dirname):
                    for item in os.listdir(dirname):
                        fullpath = os.path.join(dirname, item)
                        if os.path.isfile(fullpath):
                            ccdfile = CCDFile(fullpath, configfile=self)
                            ret[item] = ccdfile
        else:
            ret = None
        return ret

    @property
    def routes(self):
        if self._conf:
            ret = []
            iroute = self._conf.getAsArray(section=None, key='route', default=[])
            for r in iroute:
                (network, netmask) = r.split(' ', 1)
                ret.append( (network, netmask) )
        else:
            ret = None
        return ret

    @property
    def plugins(self):
        if self._conf:
            ret = []
            plugins = self._conf.getAsArray(section=None, key='plugin', default=[])
            for r in plugins:
                (plugin, plugin_params) = r.split(' ', 1)
                ret.append( (plugin, plugin_params) )
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
    def auth_user_pass(self):
        if self._conf:
            f = self._conf.get(section=None, key='auth-user-pass', default=None)
            ret = True if f else False
        else:
            ret = None
        return ret

    @auth_user_pass.setter
    def auth_user_pass(self, value):
        if self._conf is not None:
            if value:
                auth_file = None
                f = self._conf.get(section=None, key='auth-user-pass', default=None)
                if f:
                    fe = f.split(' ')
                    if len(fe) > 1:
                        auth_file = fe[1]
                self._conf.set(section=None, key='auth-user-pass', value=auth_file)
            else:
                self._conf.remove(section=None, key='auth-user-pass')

    @property
    def auth_user_pass_file(self):
        if self._conf:
            f = self._conf.get(section=None, key='auth-user-pass', default=None)
            if f:
                fe = f.split(' ')
                if len(fe) > 1:
                    ret = fe[1]
                else:
                    ret = None
            else:
                ret = None
        else:
            ret = None
        return ret

    @auth_user_pass_file.setter
    def auth_user_pass_file(self, value):
        if self._conf is not None:
            self._conf.set(section=None, key='auth-user-pass', value=value)

    def client_config_file(self, client_ccdfile=None):
        if not self.server:
            return None
        
        keepalive_ping, keepalive_pingrestart = self.keepalive

        cert_line = ''
        key_line = ''
        ca_line = ''
        dh_line = ''
        crl_line = ''
        if client_ccdfile and client_ccdfile.certfile:
            cert_line = 'cert %s' % (client_ccdfile.certfile)
        if client_ccdfile and client_ccdfile.keyfile:
            key_line = 'key %s' % (client_ccdfile.keyfile)
        if self.ca_filename:
            abspath = os.path.join(self.config_directory, self.ca_filename)
            ca_line = 'ca %s' % abspath
        if self.dh_filename:
            abspath = os.path.join(self.config_directory, self.dh_filename)
            dh_line = 'dh %s' % abspath
        if self.crl_filename:
            abspath = os.path.join(self.config_directory, self.crl_filename)
            crl_line = 'crl-verify %s' % abspath

        if 'openvpn-auth-pam.so' in self.plugins:
            if client_ccdfile and client_ccdfile.auth_user_pass_file:
                server_auth = "auth-user-pass %s" % (client_ccdfile.auth_user_pass_file)
            else:
                server_auth = "auth-user-pass"
        else:
            server_auth = ''

        routes = []
        clientname = 'unknown'
        clientostype = 'unknown'
        if client_ccdfile:
            for (network, netmask) in client_ccdfile.routes:
                routes.append('route %s %s' % (network, netmask))
            clientname = client_ccdfile.name
            clientostype = client_ccdfile.ostype

        template_buf = """
#
# THIS FILE IS AUTOMATICALLY GENERATED BY
# %(generator)s
#
# name %(clientname)s
# ostype %(clientostype)s
client
remote %(public_address)s %(public_port)i
ns-cert-type server
nobind
proto %(protocol)s
dev tun
cipher %(cipher)s
verb 1
mute 20
keepalive %(keepalive_ping)i %(keepalive_pingrestart)i
resolv-retry infinite

comp-lzo
float
persist-tun
persist-key
persist-local-ip
persist-remote-ip
push "persist-key"
push "persist-tun"

%(cert_line)s
%(key_line)s
%(ca_line)s
%(dh_line)s
%(crl_line)s

%(server_auth)s
%(routes)s

#
# EOF
#
""" % {
    'generator': __name__,
    'clientname': clientname,
    'clientostype': clientostype,
    'protocol': self.protocol,
    'cipher': self.cipher,
    'public_address': self.public_address,
    'public_port': self.public_port,
    'cert_line': cert_line,
    'key_line': key_line,
    'ca_line': ca_line,
    'dh_line': dh_line,
    'crl_line': crl_line,
    'keepalive_ping':keepalive_ping, 
    'keepalive_pingrestart':keepalive_pingrestart,
    'server_auth':server_auth,
    'routes':'\n'.join(routes)
        }
        zip_cfgfile_stream = StringIO.StringIO(template_buf)
        return ConfigFile(zip_cfgfile_stream)

    def __str__(self):
        ret = "name: " + str(self.name) + "\r\n" +\
            "config file: " + str(self.filename) + "\r\n" +\
            "conf file: " + str(self._conf.filename) + "\r\n" +\
            "status file: " + str(self.status_file) + "\r\n" +\
            "status version: " + str(self.status_version) + "\r\n" +\
            "status interval: " + str(self.status_interval) + "\r\n" +\
            "client: " + str(self.client) + "\r\n" +\
            "server: " + str(self.server) + "\r\n" +\
            "management: " + str(self.management) + "\r\n" +\
            "management_socket: " + str(self.management_socket) + "\r\n" +\
            "remote: " + str(self.remote) + "\r\n" +\
            "local: " + str(self.local) + "\r\n" +\
            "protocol: " + str(self.protocol) + "\r\n" +\
            "cipher: " + str(self.cipher) + "\r\n" +\
            "public_address: " + str(self.public_address) + "\r\n" +\
            "public_port: " + str(self.public_port) + "\r\n" +\
            "keepalive: " + str(self.keepalive) + "\r\n" +\
            "crl_file: " + str(self.crl_file) + "\r\n" +\
            "dh_file: " + str(self.dh_file) + "\r\n" +\
            "ca_file: " + str(self.ca_file) + "\r\n" +\
            "cert_file: " + str(self.cert_file) + "\r\n" +\
            "key_file: " + str(self.key_file) + "\r\n" +\
            "push_options: " + str(self.push_options) + "\r\n" +\
            "routes: " + str(self.routes) + "\r\n" +\
            "plugins: " + str(self.plugins) + "\r\n" +\
            "auth_user_pass: " + str(self.auth_user_pass) + "\r\n" +\
            "auth_user_pass_file: " + str(self.auth_user_pass_file) + "\r\n" +\
            "client-config-dir: " + str(self.client_config_directory) + "\r\n" +\
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
