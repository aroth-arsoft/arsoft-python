#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which, runcmdAndGetData

import tempfile
import sys

class ImapBackupPluginConfig(BackupPluginConfig):

    class AccountItem(object):
        def __init__(self, name, username, password,
                     master_username=None,
                     master_password=None,
                     server=None, server_type=None, ssl=False, mechanisms=None,
                     readonly=True):
            self.name = name
            self.username = username
            self.password = password
            self.master_username = master_username
            self.master_password = master_password
            self.server = server
            self.server_type = server_type
            self.ssl = ssl
            self.mechanisms = mechanisms
            self.readonly = readonly

        def __str__(self):
            return '%s (%s@%s)' % (self.name, self.username, self.server)

        def local_config(self, base_dir):
            items = { 'type': 'Maildir' }
            items['localfolders'] = os.path.join(base_dir, self.maildata_dir)
            ret = ''
            for k,v in items.items():
                ret += '%s = %s\n' % (k,v)
            return ret

        def remote_config(self):
            items = { 'type': 'IMAP' }
            items['remotehost'] = self.server
            if self.master_username is not None:
                if self.server_type == 'Dovecot':
                    items['remoteuser'] = '%s*%s' % (self.username, self.master_username)
                elif self.server_type == 'Cyrus':
                    items['remoteuser'] = self.username
                    items['remote_identity'] = self.master_username
                items['remotepass'] = self.master_password
            else:
                items['remotepass'] = self.password
            if self.mechanisms is not None:
                if isinstance(self.mechanisms, str):
                    items['auth_mechanisms'] = self.mechanisms
                else:
                    items['auth_mechanisms'] = ','.join(self.mechanisms)
            items['ssl'] = 'yes' if self.ssl else 'no'
            items['readonly'] = 'True' if self.readonly else 'False'

            ret = ''
            for k,v in items.items():
                ret += '%s = %s\n' % (k,v)
            return ret

        @property
        def config_file(self):
            return '%s.conf' % self.name

        @property
        def metadata_dir(self):
            return 'meta-%s' % self.name

        @property
        def maildata_dir(self):
            return '%s' % self.name


    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'imap')
        self._account_list = []

    @property
    def account_list(self):
        return self._account_list

    @account_list.setter
    def account_list(self, value):
        self._account_list = value

    def _read_conf(self, inifile):
        master_username = inifile.get(None, 'master_username', None)
        master_password = inifile.get(None, 'master_password', None)
        default_server = inifile.get(None, 'server', None)
        default_server_type = inifile.get(None, 'server_type', 'Dovecot')
        for sect in inifile.sections:
            username = inifile.get(sect, 'username', None)
            password = inifile.get(sect, 'password', None)
            server = inifile.get(sect, 'server', default_server)
            server_type = inifile.get(sect, 'server_type', default_server_type)

            if username and (password or master_password) and server:
                account = ImapBackupPluginConfig.AccountItem(
                    name=sect,
                    username=username,
                    password=password,
                    master_username=master_username,
                    master_password=master_password,
                    server=server,
                    server_type=server_type,
                    )
                self._account_list.append(account)
        return True
    
    def _write_conf(self, inifile):
        return True

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        ret = ret + 'accounts:\n'
        if self._account_list:
            for item in self._account_list:
                ret = ret + '  %s\n' % (item)
        return ret

class ImapBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = ImapBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'imap')
        self.offlineimap_exe = which('offlineimap', only_first=True)

    def _write_offlineimap_config(self, backup_dir, account):
        ret = None
        filename = os.path.join(backup_dir, account.config_file)
        metadata_dir = os.path.join(backup_dir, account.metadata_dir)
        try:
            f = open(filename, 'w')
            f.write("""[general]
accounts = %(accountname)s
metadata = %(metadata_dir)s
sslcacertfile = /etc/ssl/certs/ca-certificates.crt

[Account %(accountname)s]
localrepository = %(accountname)s-local
remoterepository = %(accountname)s-remote
status_backend = sqlite

[Repository %(accountname)s-local]
%(local_config)s
[Repository %(accountname)s-remote]
%(remote_config)s
""" % { 'accountname': account.name,
                       'metadata_dir': metadata_dir,
                        'remote_config': account.remote_config(),
                        'local_config': account.local_config(backup_dir),
                        } )
            f.close()
            ret = filename
        except IOError as e:
            pass
        return ret


    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret and self.offlineimap_exe is not None:
            imap_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for item in self.config.account_list:
                if self.backup_app._verbose:
                    print('backup %s' % str(item))

                conf_file = self._write_offlineimap_config(backup_dir, item)
                if not conf_file:
                    self.writelog('Failed to generate config file for %s' % (item.name))
                else:
                    args=[self.offlineimap_exe, '-c', conf_file]
                    (sts, stdout_data, stderr_data) = runcmdAndGetData(args, outputStdErr=False, outputStdOut=False, verbose=self.backup_app._verbose)
                    if sts == 0:
                        if self.backup_app._verbose:
                            print('backup %s complete' % str(item.name))
                        maildata_dir = os.path.join(backup_dir, item.maildata_dir)
                        imap_backup_filelist.append(maildata_dir)

                        metadata_dir = os.path.join(backup_dir, item.metadata_dir)
                        imap_backup_filelist.append(metadata_dir)

            #print(imap_backup_filelist)
            self.backup_app.append_to_filelist(imap_backup_filelist)
            #print(self.intermediate_filelist)
        return ret
 
