#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which
from arsoft.sshutils import SudoSessionException
import hashlib
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

    def _update_dump_file(self, dest_file, dump_data):
        m = hashlib.md5()
        m.update(dump_data)
        new_checksum = m.hexdigest()

        old_checksum = None
        try:
            f = open(dest_file + '.md5', 'r')
            old_checksum = f.read().strip()
            f.close()
        except IOError:
            pass

        ret = True
        if old_checksum != new_checksum:
            try:
                f = open(dest_file, 'w')
                f.write(dump_data.decode())
                # protect the file content (includes passwords and other sensitive information)
                # from the rest of the world.
                os.fchmod(f.fileno(), 0o600)
                f.close()
                f = open(dest_file + '.md5', 'w')
                f.write(new_checksum)
                # same for checksump file not necessary, but looks better.
                os.fchmod(f.fileno(), 0o600)
                f.close()
            except IOError:
                ret = False
        return ret

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

                slapd_dumpfile = os.path.join(backup_dir, server.name + '.ldif')
                slapd_checksumfile = slapd_dumpfile + '.md5'

                slapd_dump_data = None
                exe = 'slapcat'
                if self.backup_app.is_localhost(server.hostname):
                    if self.slapcat_exe is None:
                        sys.stderr.write('Unable to find slapcat executable for local LDAP backup of server %s.\n' % str(server))
                        ret = False
                    else:
                        exe = self.slapcat_exe

                if ret:
                    if self.backup_app._verbose:
                        print('backup remote LDAP server %s' % server.hostname)

                    server_item = self.backup_app.find_remote_server_entry(hostname=server.hostname)
                    if self.backup_app._verbose:
                        print('use remote server %s' % str(server_item))
                    if server_item:
                        cxn = server_item.connection
                        try:
                            (sts, stdout_data, stderr_data) = cxn.runcmdAndGetData(args=[exe], sudo=True, outputStdErr=False, outputStdOut=False)
                            if sts != 0:
                                sys.stderr.write('slapcat failed, error %s\n' % stderr_data)
                                ret = False
                            else:
                                slapd_dump_data = stdout_data
                        except SudoSessionException as e:
                            sys.stderr.write('slapcat failed, because sudo failed: %s.\n' % str(e))
                            ret = False
                if ret and slapd_dump_data:
                    ret = self._update_dump_file(slapd_dumpfile, slapd_dump_data)
                    if ret:
                        slapd_backup_filelist.append(slapd_dumpfile)
                        slapd_backup_filelist.append(slapd_checksumfile)

            self.backup_app.append_to_filelist(slapd_backup_filelist)
        return ret
