#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which, runcmdAndGetData, get_gid, get_uid, walk_filetree, create_posix_acl, apply_access_to_parent_directories
from arsoft.sshutils import SudoSessionException
from arsoft.rsync import Rsync

import tempfile
import sys
import stat

class DovecotBackupPluginConfig(BackupPluginConfig):

    class AccountItem(object):
        def __init__(self, enabled, name, username, password,
                     master_username=None,
                     master_password=None,
                     server=None, server_type=None, ssl=False, mechanisms=None,
                     readonly=True):
            self.enabled = enabled
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
            return '%s (%s on %s)' % (self.name, self.username, self.server)

        def local_config(self, base_dir):
            items = { 'type': 'Maildir' }
            items['localfolders'] = os.path.join(base_dir, self.maildata_dir)
            items['sep'] = '/'
            ret = ''
            for k,v in items.items():
                ret += '%s = %s\n' % (k,v)
            return ret

        @property
        def is_valid(self):
            return self.name is not None and self.username is not None and self.server is not None

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
            # DO NOT backup the backups
            items['folderfilter'] = 'lambda folder: not folder.startswith(\'backup\')'

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

        @property
        def domain(self):
            idx = self.username.find('@')
            if idx > 0:
                return self.username[idx+1:]
            else:
                return None

        @property
        def user(self):
            idx = self.username.find('@')
            if idx > 0:
                return self.username[0:idx]
            else:
                return self.username

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'dovecot')
        self._account_list = []

    @property
    def account_list(self):
        return self._account_list

    @account_list.setter
    def account_list(self, value):
        self._account_list = value

    def _read_conf(self, inifile):
        self.master_password = inifile.get(None, 'master_password', None)
        if self.master_password is not None:
            self.master_username = inifile.get(None, 'master_username', 'doveadm')
        else:
            self.master_username = None
        self.default_server = inifile.get(None, 'server', self.backup_app.fqdn)
        self.default_server_type = inifile.get(None, 'server_type', 'Dovecot')
        self.mail_uid = inifile.get(None, 'mail_uid', 'vmail')
        self.mail_gid = inifile.get(None, 'mail_gid', 'vmail')
        self.backup_mail_location = inifile.get(None, 'backup_mail_location', 'maildir:/var/vmail/backup/%d/%n')
        self.load_accounts_automatically = inifile.get(None, 'load_accounts_automatically', True)
        for sect in inifile.sections:
            enabled = inifile.get(sect, 'enabled', True)
            username = inifile.get(sect, 'username', None)
            password = inifile.get(sect, 'password', None)
            server = inifile.get(sect, 'server', self.default_server)
            server_type = inifile.get(sect, 'server_type', self.default_server_type)

            if username and (password or self.master_password) and server:
                account = DovecotBackupPluginConfig.AccountItem(
                    enabled=enabled,
                    name=sect,
                    username=username,
                    password=password,
                    master_username=self.master_username,
                    master_password=self.master_password,
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

class DovecotBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = DovecotBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'dovecot')
        self.offlineimap_exe = which('offlineimap', only_first=True)
        self.doveadm_exe = which('doveadm', only_first=True)
        self._account_list = None

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

    def _prepare_dovecot_acls(self, backup_dir):

        ret = True
        mail_uid = get_uid(self.config.mail_uid)
        mail_gid = get_gid(self.config.mail_gid)

        if mail_uid != 0 or mail_gid != 0:
            self._dir_acl, self._file_acl = create_posix_acl(file=backup_dir, uid=mail_uid, gid=mail_gid)
            if self._dir_acl is None:
                self.writelog('Unable to create directory ACL for dovecot to access the backup at %s.\n' % (backup_dir))
                ret = False
            if self._file_acl is None:
                self.writelog('Unable to create file ACL for dovecot to access the backup at %s.\n' % (backup_dir))
                ret = False

        return ret

    def _grant_dovecot_backup_access(self, backup_dir, recursive=True):
        if self._dir_acl is None or self._file_acl is None:
            return False

        ret = False
        class _apply_acls(object):
            def __init__(self, dir_acl, file_acl):
                self._dir_acl = dir_acl
                self._file_acl = file_acl
            def __call__(self, path, stats):
                try:
                    if stat.S_ISDIR(stats.st_mode):
                        #print('set dir acl=%s' % path)
                        self._dir_acl.applyto(path)
                    else:
                        #print('set file acl=%s' % path)
                        self._file_acl.applyto(path)
                    return True
                except OSError as e:
                    #print('failed to set acl to %s: %s' % (path, e))
                    return False

        #print(dir_acl)
        #print(file_acl)

        self._dir_acl.applyto(backup_dir)
        if recursive:
            walk_filetree(backup_dir, operation=_apply_acls(self._dir_acl, self._file_acl))

        return ret

    def start_backup(self, **kwargs):
        if self.doveadm_exe is None:
            self.writelog('doveadm not found')
            return False

        # take over configured account list
        self._account_list = self.config.account_list
        self._backup_mail_location = self.config.backup_mail_location
        if self._backup_mail_location is not None:
            if ':' in self._backup_mail_location:
                (scheme, self._backup_mail_location) = self._backup_mail_location.split(':', 1)
                if scheme != 'maildir':
                    self._backup_mail_location = None

        if self.backup_app.root_dir is not None and self._backup_mail_location is not None:
            if self.backup_app.root_dir != '/':
                self._backup_mail_location = self.backup_app.root_dir + self._backup_mail_location

        self._prepare_dovecot_acls(self.backup_app.backup_dir)

        ret = False
        localhost_server_item = self.backup_app.find_remote_server_entry(hostname='localhost')
        if self.backup_app._verbose:
            print('use server %s' % str(localhost_server_item))
        if localhost_server_item:
            cxn = localhost_server_item.connection
        if self.config.load_accounts_automatically:
            try:
                (sts, stdout_data, stderr_data) = cxn.runcmdAndGetData(args=[self.doveadm_exe, 'user', '*'], sudo=True, outputStdErr=False, outputStdOut=False)
                if sts == 0:
                    for line in stdout_data.splitlines():
                        name = line.decode('utf8').strip()
                        if not name:
                            continue
                        account = DovecotBackupPluginConfig.AccountItem(
                            enabled=True,
                            name=name,
                            username=name,
                            password=None,
                            master_username=self.config.master_username,
                            master_password=self.config.master_password,
                            server=self.config.default_server,
                            server_type=self.config.default_server_type,
                            )
                        if account.is_valid:
                            if self.backup_app._verbose:
                                print('add account %s' % (account))
                            self._account_list.append(account)
                        else:
                            self.writelog('Got invalid account %s' % (account) )
                    ret = True
                else:
                    self.writelog('Unable to get account list from doveadm (Exit code %i, %s)' % (sts, stderr_data.strip()) )
            except SudoSessionException as e:
                self.writelog('Unable to get account list from doveadm because sudo failed: %s.\n' % str(e))
        return ret

    def perform_backup(self, **kwargs):
        if self._account_list is None:
            self.writelog('Account list is empty')
            return False

        ret = True

        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            if self.offlineimap_exe is None:
                self.writelog('offlineimap not found')
                ret = False
            else:
                dovecot_backup_filelist = FileListItem(base_directory=self.config.base_directory)
                for item in self._account_list:
                    if self.backup_app._verbose:
                        print('backup %s' % str(item))

                    if not item.enabled:
                        if self.backup_app._verbose:
                            print('skip disabled %s' % str(item))
                        continue

                    if not item.is_valid:
                        if self.backup_app._verbose:
                            print('skip invalid account %s' % str(item))
                        continue

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
                            dovecot_backup_filelist.append(maildata_dir)

                            metadata_dir = os.path.join(backup_dir, item.metadata_dir)
                            dovecot_backup_filelist.append(metadata_dir)
                        else:
                            self.writelog('Failed to backup dovecot account %s; Error %i: %s' % (item.name, sts, stderr_data.decode('utf8')))

                if not self._grant_dovecot_backup_access(backup_dir):
                    ret = False

                #print(dovecot_backup_filelist)
                self.backup_app.append_to_filelist(dovecot_backup_filelist)
                #print(self.intermediate_filelist)
        return ret

    def _get_mail_location_without_account(self):
        base_path=[]
        for e in self._backup_mail_location.split('/'):
            if not '%' in e:
                base_path.append(e)
        return '/'.join(base_path)

    def _expand_mail_location(self, account):
        ret = self._backup_mail_location
        if '%d' in ret:
            if account.domain is None:
                return None
            ret = ret.replace('%d', account.domain)
        if '%n' in ret:
            if account.user is None:
                return None
            ret = ret.replace('%n', account.user)
        if '%u' in ret:
            if account.username is None:
                return None
            ret = ret.replace('%u', account.username)
        return ret

    def rsync_complete(self, **kwargs):
        backup_dir = self.backup_app.session.backup_dir
        if backup_dir is None or not backup_dir:
            self.writelog('No backup directory.')
            return False
        ret = True

        if Rsync.is_rsync_url(backup_dir):
            print('Cannot map backup to %s into dovecot namespace at %s' % (backup_dir, self._backup_mail_location))
        else:
            backup_name = self.backup_app.session.backup_name

            if backup_dir and backup_dir[-1] != '/':
                backup_dir += '/'
            backup_dir = os.path.join(backup_dir, 'dovecot')

            # grant dovecot access to the base backup directory (for this session)
            # and access to directories above
            mail_uid = get_uid(self.config.mail_uid)
            mail_gid = get_gid(self.config.mail_gid)

            if (mail_uid != 0 or mail_gid != 0) and os.path.isdir(backup_dir):
                apply_access_to_parent_directories(backup_dir, uid=mail_uid, gid=mail_gid)

            for item in self._account_list:
                if self.backup_app._verbose:
                    print('backup %s' % (item.name))

                if not item.enabled or not item.is_valid:
                    if self.backup_app._verbose:
                        print('skip disabled or invalid account %s' % (item.name))
                    continue

                src_dir = os.path.join(backup_dir, item.maildata_dir)
                account_dir = self._expand_mail_location(item)
                if account_dir is None:
                    self.writelog('Unable to get backup directory for dovecot account %s from %s' % (item.name, item.maildata_dir))
                else:
                    if not os.path.isdir(account_dir):
                        os.makedirs(account_dir)
                    account_dir = os.path.join(account_dir, backup_name)

                    self.writelog('create link from %s -> %s' % (src_dir, account_dir))
                    self.backup_app.create_link(src_dir, account_dir, symlink=True)

        return ret

    def manage_retention_complete(self, **kwargs):
        backup_dir = self.backup_app.session.backup_dir
        if backup_dir is None or not backup_dir:
            self.writelog('No backup directory.')
            return False

        if Rsync.is_rsync_url(backup_dir):
            print('Cannot map backup to %s into dovecot namespace at %s' % (backup_dir, self._backup_mail_location))
        else:
            for item in self._account_list:
                if self.backup_app._verbose:
                    print('manage_retention for account %s' % str(item))
                src_dir = os.path.join(backup_dir, item.maildata_dir)
                account_dir = self._expand_mail_location(item)
                if account_dir is None:
                    self.writelog('Unable to get backup directory for dovecot account %s from %s' % (item.name, item.maildata_dir))
                else:
                    if not os.path.isdir(account_dir):
                        continue
                    for f in os.listdir(account_dir):
                        full = os.path.join(account_dir, f)
                        if os.path.islink(full):
                            target = os.readlink(full)
                            target_full = os.path.normpath(os.path.join(account_dir, target))
                            if not os.path.isdir(target_full):
                                self.writelog('Remove link to %s for dovecot account %s' % (target_full, item.name))
                                os.unlink(full)
        return True

