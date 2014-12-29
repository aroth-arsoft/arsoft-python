#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which
from arsoft.sshutils import ssh_runcmdAndGetData
import tempfile
import sys

class SlapdBackupPluginConfig(BackupPluginConfig):

    class ServerInstance(object):
        def __init__(self, name, hostname, port=22, username='root', password=''):
            self.name = name
            self.hostname = hostname
            self.port = port
            self.username = username
            self.password = password

        def __str__(self):
            return '%s (%s:***@%s:%i)' % (self.name, self.username, self.hostname, self.port)

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'slapd')
        self._server_list = []

    @property
    def server_list(self):
        return self._server_list

    @server_list.setter
    def server_list(self, value):
        self._server_list = value

    def _read_conf(self, inifile):
        for sect in inifile.sections:
            hostname = inifile.get(sect, 'host', None)
            port = inifile.getAsInteger(sect, 'port', 22)
            username = inifile.get(sect, 'username', None)
            password = inifile.get(sect, 'password', None)
            if hostname:
                self._server_list.append(SlapdBackupPluginConfig.ServerInstance(sect,
                                                                                hostname=hostname, port=port,
                                                                                username=username, password=password))
        return True

    def _write_conf(self, inifile):
        return True

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        ret = ret + 'servers:\n'
        if self._server_list:
            for item in self._server_list:
                ret = ret + '  %s:\n' % item.name
                ret = ret + '    server: %s:%i\n' % (item.hostname, item.port)
                ret = ret + '    username: %s\n' % item.username
                ret = ret + '    password: %s\n' % item.password
        return ret

class SlapdBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = SlapdBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'slapd')
        self.slapcat_exe = which('slapcat', only_first=True)

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            slapd_backup_filelist = FileListItem(base_directory=self.config.base_directory)

            for server in self.config.server_list:
                if self.backup_app._verbose:
                    print('backup LDAP server %s' % str(server))

                if self.backup_app.is_localhost(server.hostname):
                    if self.slapcat_exe is None:
                        sys.stderr.write('Unable to find slapcat for local LDAP backup.')
                        ret = False
                    else:
                        if self.backup_app._verbose:
                            print('backup local LDAP server %s' % server.hostname)
                        pass
                else:
                    if self.backup_app._verbose:
                        print('backup remote LDAP server %s' % server.hostname)

                    script="""
slapcat -v -l
                    """
                    ssh_runcmdAndGetData(script=

            self.backup_app.append_to_filelist(slapd_backup_filelist)
        return ret
