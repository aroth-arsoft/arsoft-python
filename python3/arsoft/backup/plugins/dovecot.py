#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.utils import which, runcmdAndGetData, get_gid, get_uid, walk_filetree, create_posix_acl, apply_access_to_parent_directories
from arsoft.sshutils import SudoSessionException
from arsoft.rsync import Rsync
from arsoft.offlineimap import OfflineImap

import tempfile
import sys
import stat

class DovecotBackupPluginConfig(BackupPluginConfig):

    def __init__(self, plugin, parent):
        BackupPluginConfig.__init__(self, parent, 'dovecot')
        self._plugin = plugin

    @property
    def account_list(self):
        return self._account_list

    @account_list.setter
    def account_list(self, value):
        self._account_list = value

    def _read_conf(self, inifile):
        self.mail_uid = inifile.get(None, 'mail_uid', 'vmail')
        self.mail_gid = inifile.get(None, 'mail_gid', 'vmail')
        self.backup_mail_location = inifile.get(None, 'backup_mail_location', 'maildir:/var/vmail/backup/%d/%n')
        self.load_accounts_automatically = inifile.get(None, 'load_accounts_automatically', True)
        self.use_sudo = inifile.get(None, 'use_sudo', True)
        self.server = inifile.get(None, 'server', self.backup_app.fqdn)
        self.port = inifile.get(None, 'port', 143)
        self.master_username = inifile.get(None, 'master_username', 'doveadm')
        self.master_password = inifile.get(None, 'master_password', None)
        return self._plugin._offlineimap.readConfig(inifile)
    
    def _write_conf(self, inifile):
        return True

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        ret = ret + 'mail_uid: ' + str(self.mail_uid) + '\n'
        ret = ret + 'mail_gid: ' + str(self.mail_gid) + '\n'
        ret = ret + 'backup_mail_location: ' + str(self.backup_mail_location) + '\n'
        ret = ret + 'load_accounts_automatically: ' + str(self.load_accounts_automatically) + '\n'
        ret = ret + 'use_sudo: ' + str(self.use_sudo) + '\n'
        ret = ret + 'server: ' + str(self.server) + '\n'
        ret = ret + 'port: ' + str(self.port) + '\n'
        ret = ret + 'master_username: ' + str(self.master_username) + '\n'
        ret = ret + 'master_password: ' + str(self.master_password) + '\n'
        ret = ret + 'accounts:\n'
        if self._plugin._offlineimap.account_list:
            for item in self._plugin._offlineimap.account_list:
                ret = ret + '  %s\n' % (item)
        return ret

class DovecotBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self._offlineimap = OfflineImap()
        self.config = DovecotBackupPluginConfig(self, backup_app)
        BackupPlugin.__init__(self, backup_app, 'dovecot')
        self.doveadm_exe = which('doveadm', only_first=True)
        self._account_list = []
        self._backup_mail_location = None
        self._dir_acl = None 
        self._file_acl = None

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

        try:
            self._dir_acl.applyto(backup_dir)
            ret = True
        except PermissionError as e:
            self.writelog('Unable to set ACL for dovecot to access the backup at %s, error %s.\n' % (backup_dir, e))
            pass

        if ret and recursive:
            walk_filetree(backup_dir, operation=_apply_acls(self._dir_acl, self._file_acl))

        return ret

    def start_backup(self, **kwargs):
        if self.doveadm_exe is None:
            self.writelog('doveadm not found')
            return False

        # take over configured account list
        self._account_list = self._offlineimap.account_list
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
            if cxn is None:
                self.writelog('Unable to get local connection; unable to retrieve mail account information.\n')
            else:
                try:
                    (sts, stdout_data, stderr_data) = cxn.runcmdAndGetData(args=[self.doveadm_exe, 'user', '*'], sudo=self.config.use_sudo, outputStdErr=False, outputStdOut=False)
                    if sts == 0:
                        for line in stdout_data.splitlines():
                            name = line.decode('utf8').strip()
                            if not name:
                                continue
                            local = { 'server_type': 'Maildir', 'maildir': name }
                            remote = { 'server_type': 'Dovecot', 'server': self.config.server, 'port':self.config.port, 'username': name }
                            if self.config.master_username and self.config.master_password:
                                remote['master_username'] = self.config.master_username
                                remote['master_password'] = self.config.master_password

                            account = OfflineImap.AccountItem(
                                enabled=True,
                                name=name,
                                local=local,
                                remote=remote
                                )
                            if self._offlineimap.add_account(account):
                                if self.backup_app._verbose:
                                    print('add account %s' % (account))
                            else:
                                self.writelog('Got invalid account %s' % (account) )
                                if not account.local.is_valid:
                                    self.writelog('Got invalid local account config %s' % (account.local) )
                                if not account.remote.is_valid:
                                    self.writelog('Got invalid remote account config %s' % (account.remote) )
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
            if not self._offlineimap.is_installed:
                self.writelog('offlineimap not installed')
                ret = False
            else:
                dovecot_backup_filelist = FileListItem(base_directory=self.config.base_directory)
                for item in self._offlineimap.account_list:
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

                    if self._offlineimap.run(account=item, base_dir=backup_dir, log=self.logfile_proxy):
                        if self.backup_app._verbose:
                            print('backup %s complete' % str(item.name))
                        maildata_dir = os.path.join(backup_dir, item.local.maildir)
                        dovecot_backup_filelist.append(maildata_dir)

                        metadata_dir = os.path.join(backup_dir, item.metadata_dir)
                        dovecot_backup_filelist.append(metadata_dir)
                    else:
                        self.writelog('Failed to backup dovecot account %s; using config %s' % (item.name, self._offlineimap.config_file))

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
            if account.remote.domain is None:
                return None
            ret = ret.replace('%d', account.remote.domain)
        if '%n' in ret:
            if account.remote.user is None:
                return None
            ret = ret.replace('%n', account.remote.user)
        if '%u' in ret:
            if account.remote.username is None:
                return None
            ret = ret.replace('%u', account.remote.username)
        return ret

    def rsync_complete(self, **kwargs):
        backup_dir = self.backup_app.session.backup_dir
        if backup_dir is None or not backup_dir:
            self.writelog('No backup directory.')
            return False
        ret = True

        if Rsync.is_rsync_url(backup_dir):
            if self._backup_mail_location:
                self.writelog('Cannot map rsync backup to %s into dovecot namespace at %s' % (backup_dir, self._backup_mail_location))
            else:
                self.writelog('Cannot map rsync backup to %s into dovecot' % (backup_dir))
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

                src_dir = os.path.join(backup_dir, item.name)
                account_dir = self._expand_mail_location(item)
                if account_dir is None:
                    self.writelog('Unable to get backup directory for dovecot account %s' % (item.name))
                else:
                    if not os.path.isdir(account_dir):
                        os.makedirs(account_dir)
                    account_dir = os.path.join(account_dir, backup_name)
                    if os.path.isdir(src_dir):
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
                src_dir = os.path.join(backup_dir, item.name)
                account_dir = self._expand_mail_location(item)
                if account_dir is None:
                    self.writelog('Unable to get backup directory for dovecot account %s' % (item.name))
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

