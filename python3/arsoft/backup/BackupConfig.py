#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import datetime
from arsoft.inifile import IniFile
from arsoft.filelist import *
from arsoft.socket_utils import getportbyname
from arsoft.timestamp import parse_timedelta

class BackupConfigDefaults(object):
    ROOT_DIR = None
    CONFIG_DIR = '/etc/arsoft-backup.d'
    MAIN_CONF = 'main.conf'
    SECRET_CONF = 'secret.conf'
    PRIVATE_DIR = 'private'
    CONFIG_FILE_EXTENSTION = '.conf'
    INCLUDE_DIR = 'include.d'
    EXCLUDE_DIR = 'exclude.d'
    FILESYSTEM = 'ext4'
    RETENTION_TIME_S = 86400 * 7
    RETENTION_COUNT = 7
    BACKUP_DIR = '/var/backups/arsoft-backup'
    RESTORE_DIR = None
    INTERMEDIATE_BACKUP_DIR = '/var/cache/arsoft-backup'
    EJECT_UNUSED_BACKUP_DISCS = True
    USE_FILESYSTEM_SNAPSHOTS = False
    USE_FILESYSTEM_HARDLINKS = True
    USE_SSH_FOR_RSYNC = True
    SSH_IDENTITY_FILE = None
    USE_TIMESTAMP_FOR_BACKUP_DIR = True
    TIMESTAMP_FORMAT_FOR_BACKUP_DIR = '%Y%m%d%H%M%S'
    ACTIVE_PLUGINS = ['git', 'dir', 'mysql', 'trac', 'imap', 'dovecot']
    DISK_TAG = None
    DISK_TIMEOUT = 60.0

class BackupConfig(object):

    class RemoteServerInstance(object):
        def __init__(self, name, scheme=None, hostname=None, port=None, username=None, password=None, sudo_password=None, keyfile=None):
            self.name = name
            self.scheme = scheme
            self.hostname = hostname
            self._port = port
            self.username = username
            self.password = password
            self.sudo_password = sudo_password
            self.keyfile = None

        def __str__(self):
            if self.password:
                # leave out the password
                ret = '%s (%s://%s:***@%s:%i)' % (self.name, self.scheme, self.username if self.username else 'current-user', self.hostname, self.port)
            else:
                ret = '%s (%s://%s@%s:%i)' % (self.name, self.scheme, self.username if self.username else 'current-user', self.hostname, self.port)
            if self.keyfile:
                ret = ret + ', keyfile %s' % self.keyfile
            if self.sudo_password:
                ret = ret + ', sudo *secret*'
            return ret

        @property
        def valid(self):
            return self.hostname is not None and self.scheme is not None

        @property
        def port(self):
            if self._port is not None:
                return self._port
            elif self.scheme == 'local':
                return 0
            elif self.scheme is not None:
                try:
                    return getportbyname(self.scheme)
                except OSError:
                    return 0
            else:
                return 0

        def read_conf(self, bak_config, inifile, section):
            self.scheme = inifile.get(section, 'scheme', 'local')
            self.hostname = inifile.get(section, 'host', None)
            self._port = inifile.getAsInteger(section, 'port', None)
            self.username = inifile.get(section, 'username', None)
            self.password = inifile.get(section, 'password', None)
            self.sudo_password = inifile.get(section, 'sudo-password', None)
            self.keyfile = inifile.get(section, 'keyfile', None)
            if self.keyfile:
                self.keyfile = os.path.join(bak_config.private_dir, self.keyfile)
            return self.valid

        def write_conf(self, bak_config, inifile, section):
            inifile.set(section, 'scheme', self.scheme)
            inifile.set(section, 'host', self.hostname )
            inifile.setAsInteger(section, 'port', self._port)
            inifile.set(section, 'username', self.username)
            inifile.set(section, 'password', self.password)
            inifile.set(section, 'sudo-password', self.sudo_password)
            s = os.path.relpath(self.keyfile, bak_config.private_dir) if self.keyfile else None
            inifile.set(section, 'keyfile', s)
            return True

    def __init__(self,
                 instance=None,
                 root_dir=BackupConfigDefaults.ROOT_DIR,
                 config_dir=BackupConfigDefaults.CONFIG_DIR,
                 retention_time=BackupConfigDefaults.RETENTION_TIME_S, 
                 retention_count=BackupConfigDefaults.RETENTION_COUNT,
                 backup_directory=BackupConfigDefaults.BACKUP_DIR, 
                 restore_directory=BackupConfigDefaults.RESTORE_DIR, 
                 intermediate_backup_directory=BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR, 
                 filesystem=BackupConfigDefaults.FILESYSTEM,
                 filelist_include_dir=BackupConfigDefaults.INCLUDE_DIR,
                 filelist_exclude_dir=BackupConfigDefaults.EXCLUDE_DIR,
                 private_dir=BackupConfigDefaults.PRIVATE_DIR,
                 eject_unused_backup_discs=BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS,
                 use_filesystem_snapshots=BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS,
                 use_filesystem_hardlinks=BackupConfigDefaults.USE_FILESYSTEM_HARDLINKS,
                 use_ssh_for_rsync=BackupConfigDefaults.USE_SSH_FOR_RSYNC,
                 ssh_identity_file=BackupConfigDefaults.SSH_IDENTITY_FILE,
                 use_timestamp_for_backup_dir=BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR,
                 timestamp_format_for_backup_dir=BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR,
                 active_plugins=BackupConfigDefaults.ACTIVE_PLUGINS,
                 disk_tag=BackupConfigDefaults.DISK_TAG,
                 disk_timeout=BackupConfigDefaults.DISK_TIMEOUT,
                 filelist_include=None, 
                 filelist_exclude=None):
        self.instance = instance
        self.root_dir = root_dir
        self.config_dir = config_dir
        self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
        self.secret_conf = os.path.join(config_dir, BackupConfigDefaults.SECRET_CONF)
        self.filesystem = filesystem
        self.retention_time = retention_time
        self.retention_count = retention_count
        self.backup_directory = backup_directory
        self._intermediate_backup_directory = intermediate_backup_directory
        self.filelist_include = filelist_include
        self.filelist_exclude = filelist_exclude
        self.filelist_include_dir = filelist_include_dir
        self.filelist_exclude_dir = filelist_exclude_dir
        self.private_dir = os.path.join(config_dir, private_dir)
        self.eject_unused_backup_discs = eject_unused_backup_discs
        self.use_filesystem_snapshots = use_filesystem_snapshots
        self.use_filesystem_hardlinks = use_filesystem_hardlinks
        self.use_ssh_for_rsync = use_ssh_for_rsync
        self.ssh_identity_file = ssh_identity_file
        self.use_timestamp_for_backup_dir = use_timestamp_for_backup_dir
        self.timestamp_format_for_backup_dir = timestamp_format_for_backup_dir
        self.active_plugins = active_plugins
        self.disk_tag = disk_tag
        self.disk_timeout = disk_timeout
        self._remote_servers = []

    def clear(self):
        self.instance = None
        self.root_dir = BackupConfigDefaults.ROOT_DIR
        self.config_dir = BackupConfigDefaults.CONFIG_DIR
        self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
        self.secret_conf = os.path.join(config_dir, BackupConfigDefaults.SECRET_CONF)
        self.filesystem = BackupConfigDefaults.FILESYSTEM
        self.retention_time = BackupConfigDefaults.RETENTION_TIME_S
        self.retention_count = BackupConfigDefaults.RETENTION_COUNT
        self.backup_directory = BackupConfigDefaults.BACKUP_DIR
        self._intermediate_backup_directory = BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR
        self.filelist_include = None
        self.filelist_exclude = None
        self.filelist_include_dir = BackupConfigDefaults.INCLUDE_DIR
        self.filelist_exclude_dir = BackupConfigDefaults.EXCLUDE_DIR
        self.private_dir = os.path.join(config_dir, BackupConfigDefaults.PRIVATE_DIR)
        self.eject_unused_backup_discs = BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS
        self.use_filesystem_snapshots = BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS
        self.use_filesystem_hardlinks = BackupConfigDefaults.USE_FILESYSTEM_HARDLINKS
        self.use_ssh_for_rsync = BackupConfigDefaults.USE_SSH_FOR_RSYNC
        self.ssh_identity_file = BackupConfigDefaults.SSH_IDENTITY_FILE
        self.use_timestamp_for_backup_dir = BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR
        self.timestamp_format_for_backup_dir = BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR
        self.active_plugins = BackupConfigDefaults.ACTIVE_PLUGINS
        self.disk_tag = BackupConfigDefaults.DISK_TAG
        self.disk_timeout = BackupConfigDefaults.DISK_TIMEOUT
        self._remote_servers = []

    @property
    def retention_time(self):
        return self._retention_time

    @retention_time.setter
    def retention_time(self, value):
        if value is not None:
            if isinstance(value, int):
                self._retention_time = datetime.timedelta(seconds=int(value))
            elif isinstance(value, float):
                self._retention_time = datetime.timedelta(seconds=float(value))
            elif isinstance(value, datetime.timedelta):
                self._retention_time = value
            else:
                raise ValueError('retention_time %s is invalid.' %(str(value)))
        else:
            self._retention_time = None

    @property
    def intermediate_backup_directory(self):
        return self._intermediate_backup_directory if self._intermediate_backup_directory else self.backup_directory

    @intermediate_backup_directory.setter
    def intermediate_backup_directory(self, value):
        self._intermediate_backup_directory = value

    @property
    def filelist_include(self):
        return self._filelist_include

    @property
    def filelist_exclude(self):
        return self._filelist_exclude

    @filelist_include.setter
    def filelist_include(self, value):
        if value is not None:
            if isinstance(value, FileList):
                self._filelist_include = value
            else:
                full_filename = os.path.normpath(os.path.join(self.config_dir, value))
                self._filelist_include = FileList(full_filename)
        else:
            self._filelist_include = None

    @filelist_exclude.setter
    def filelist_exclude(self, value):
        if value is not None:
            if isinstance(value, FileList):
                self._filelist_exclude = value
            else:
                full_filename = os.path.normpath(os.path.join(self.config_dir, value))
                self._filelist_exclude = FileList(full_filename)
        else:
            self._filelist_exclude = None

    @property
    def remote_servers(self):
        return self._remote_servers

    def open(self, config_dir=None, instance=None, root_dir=None):
        self.root_dir = root_dir
        self.instance = instance
        if config_dir is None:
            config_dir = self.config_dir
        else:
            if self.root_dir is not None:
                config_dir = os.path.normpath(self.root_dir + config_dir)
            if instance is not None:
                config_dir = os.path.join(config_dir, str(instance))
            self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
            self.secret_conf = os.path.join(config_dir, BackupConfigDefaults.SECRET_CONF)
            self.private_dir = os.path.join(config_dir, BackupConfigDefaults.PRIVATE_DIR)
            self.config_dir = config_dir

        if not os.path.isdir(config_dir):
            try:
                os.mkdir(config_dir)
            except OSError:
                pass

        if not os.path.isfile(self.main_conf):
            save_config_file = True
        else:
            save_config_file = False

        ret = self._read_main_conf(self.main_conf)
        if save_config_file:
            ret = self._write_main_conf(self.main_conf)

        ret = self._read_secret_conf(self.secret_conf)
        if save_config_file:
            ret = self._write_secret_conf(self.secret_conf)

        filelist_path = os.path.join(config_dir, self.filelist_include_dir)
        if not os.path.isdir(filelist_path):
            try:
                os.mkdir(filelist_path)
            except OSError:
                pass

        filelist_path = os.path.join(config_dir, self.private_dir)
        if not os.path.isdir(filelist_path):
            try:
                os.mkdir(filelist_path)
            except OSError:
                pass

        # reload the file lists
        self.filelist_include = self.filelist_include_dir
        self.filelist_exclude = self.filelist_exclude_dir

        return ret

    def save(self, config_dir=None, instance=None, root_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.root_dir = root_dir
            if self.root_dir is not None:
                config_dir = os.path.normpath(self.root_dir + config_dir)
            if instance is not None:
                config_dir = os.path.join(config_dir, str(instance))
            self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
            self.config_dir = config_dir

        ret = self._write_main_conf(self.main_conf)
        if not self._write_secret_conf(self.secret_conf):
            ret = False

        filelist_path = os.path.join(config_dir, self.filelist_include_dir)
        if self.filelist_include:
            self.filelist_include.save(filelist_path)

        filelist_path = os.path.join(config_dir, self.filelist_exclude_dir)
        if self.filelist_exclude:
            self.filelist_exclude.save(filelist_path)

        return ret

    def get_plugin_config_file(self, plugin_name):
        return os.path.join(self.config_dir, plugin_name + BackupConfigDefaults.CONFIG_FILE_EXTENSTION)

    def get_plugin_config(self, plugin_name):
        return BackupPluginConfig(self, plugin_name=plugin_name)

    def is_backup_item(self, filename):
        timestamp = None
        if self.use_timestamp_for_backup_dir:
            (basename, extension) = os.path.splitext(os.path.basename(filename))
            try:
                timestamp = datetime.datetime.strptime(basename, self.timestamp_format_for_backup_dir)
                ret = True
            except ValueError:
                ret = False
        else:
            ret = False
        return (ret, timestamp)

    def _chroot_dir(self, path):
        if path is None:
            return None
        if self.root_dir is not None:
            idx = path.find('://')
            if idx > 0:
                return path
            else:
                if self.root_dir and self.root_dir != '/':
                    return os.path.normpath(self.root_dir + path)
                else:
                    return path
        return path

    def _unchroot_dir(self, path):
        if path is None:
            return None
        if self.root_dir is not None:
            root_dir_len = len(self.root_dir)
            if path.startswith(self.root_dir):
                return path[root_dir_len:]
        return path

    def _read_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.filesystem = inifile.get(None, 'Filesystem', BackupConfigDefaults.FILESYSTEM)
        self.retention_time = None
        tmp = inifile.get(None, 'RetentionTime', BackupConfigDefaults.RETENTION_TIME_S)
        if isinstance(tmp, str):
            self.retention_time = parse_timedelta(tmp)
        if self.retention_time is None:
            self.retention_time = datetime.timedelta(seconds=float(tmp))
        self.retention_count = int(inifile.get(None, 'RetentionCount', BackupConfigDefaults.RETENTION_COUNT))
        default_backup_dir = BackupConfigDefaults.BACKUP_DIR if self.instance is None else os.path.join(BackupConfigDefaults.BACKUP_DIR, self.instance)
        self.backup_directory = self._chroot_dir(inifile.get(None, 'BackupDirectory', default_backup_dir))
        #default_restore_dir = BackupConfigDefaults.RESTORE_DIR if self.instance is None else os.path.join(BackupConfigDefaults.RESTORE_DIR, self.instance)
        default_restore_dir = BackupConfigDefaults.RESTORE_DIR
        self.restore_directory = self._chroot_dir(inifile.get(None, 'RestoreDirectory', default_restore_dir))
        default_intermediate_backup_directory = BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR if self.instance is None else os.path.join(BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR, self.instance)
        self.intermediate_backup_directory = self._chroot_dir(inifile.get(None, 'IntermediateBackupDirectory', default_intermediate_backup_directory))
        self.eject_unused_backup_discs = inifile.getAsBoolean(None, 'EjectUnusedBackupDiscs', BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS)
        self.use_filesystem_snapshots = inifile.getAsBoolean(None, 'UseFilesystemSnapshots', BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS)
        self.use_filesystem_hardlinks = inifile.getAsBoolean(None, 'UseFilesystemHardlinks', BackupConfigDefaults.USE_FILESYSTEM_HARDLINKS)
        self.use_ssh_for_rsync = inifile.getAsBoolean(None, 'UseSSHForRsync', BackupConfigDefaults.USE_SSH_FOR_RSYNC)
        self.ssh_identity_file = self._chroot_dir(inifile.get(None, 'SSHIdentityFile', BackupConfigDefaults.SSH_IDENTITY_FILE))
        self.use_timestamp_for_backup_dir = inifile.getAsBoolean(None, 'UseTimestampForBackupDir', BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR)
        self.timestamp_format_for_backup_dir = inifile.get(None, 'TimestampFormatForBackupDir', BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR)
        self.filelist_include_dir = self._chroot_dir(inifile.get(None, 'FileListIncludeDirectory', BackupConfigDefaults.INCLUDE_DIR))
        self.filelist_exclude_dir = self._chroot_dir(inifile.get(None, 'FileListExcludeDirectory', BackupConfigDefaults.EXCLUDE_DIR))
        self.active_plugins = inifile.getAsArray(None, 'ActivePlugins', BackupConfigDefaults.ACTIVE_PLUGINS)
        self.disk_tag = inifile.get(None, 'DiskTag', BackupConfigDefaults.DISK_TAG)
        self.disk_timeout = inifile.get(None, 'DiskTimeout', BackupConfigDefaults.DISK_TIMEOUT)
        return ret

    def _write_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config
        inifile.set(None, 'Filesystem', self.filesystem)
        inifile.set(None, 'RetentionTime', self.retention_time.total_seconds())
        inifile.set(None, 'RetentionCount', self.retention_count)
        inifile.set(None, 'BackupDirectory', self._unchroot_dir(self.backup_directory))
        inifile.set(None, 'RestoreDirectory', self._unchroot_dir(self.restore_directory))
        inifile.set(None, 'IntermediateBackupDirectory', self._unchroot_dir(self._intermediate_backup_directory))
        inifile.setAsBoolean(None, 'EjectUnusedBackupDiscs', self.eject_unused_backup_discs)
        inifile.setAsBoolean(None, 'UseFilesystemSnapshots', self.use_filesystem_snapshots)
        inifile.setAsBoolean(None, 'UseFilesystemHardlinks', self.use_filesystem_hardlinks)
        inifile.setAsBoolean(None, 'UseSSHForRsync', self.use_ssh_for_rsync)
        inifile.set(None, 'SSHIdentityFile', self._unchroot_dir(self.ssh_identity_file))
        inifile.setAsBoolean(None, 'UseTimestampForBackupDir', self.use_timestamp_for_backup_dir)
        inifile.set(None, 'TimestampFormatForBackupDir', self.timestamp_format_for_backup_dir)
        inifile.set(None, 'FileListIncludeDirectory', self._unchroot_dir(self.filelist_include_dir))
        inifile.set(None, 'FileListExcludeDirectory', self._unchroot_dir(self.filelist_exclude_dir))
        inifile.set(None, 'ActivePlugins', self.active_plugins)
        inifile.set(None, 'DiskTag', self.disk_tag)
        inifile.set(None, 'DiskTimeout', self.disk_timeout)

        ret = inifile.save(filename)
        return ret

    def _read_secret_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)

        for section in inifile.sections:
            inst = BackupConfig.RemoteServerInstance(name=section)
            if inst.read_conf(self, inifile, section):
                self._remote_servers.append(inst)
        return ret

    def _write_secret_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config

        for inst in self._remote_servers:
            inst.write_conf(self, inifile, inst.name)

        ret = inifile.save(filename)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'root directory: ' + str(self.root_dir) + '\n'
        ret = ret + 'filesystem: ' + str(self.filesystem) + '\n'
        ret = ret + 'backup directory: ' + str(self.backup_directory) + '\n'
        ret = ret + 'restore directory: ' + str(self.restore_directory) + '\n'
        ret = ret + 'intermediate backup directory: ' + str(self.intermediate_backup_directory) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        ret = ret + 'retention count: ' + str(self.retention_count) + '\n'
        ret = ret + 'include file list: ' + str(self._filelist_include) + '\n'
        ret = ret + 'exclude file list: ' + str(self._filelist_exclude) + '\n'
        ret = ret + 'eject unused backup discs: ' + str(self.eject_unused_backup_discs) + '\n'
        ret = ret + 'use filesystem snapshots: ' + str(self.use_filesystem_snapshots) + '\n'
        ret = ret + 'use filesystem hardlinks: ' + str(self.use_filesystem_hardlinks) + '\n'
        ret = ret + 'use ssh for rsync: ' + str(self.use_ssh_for_rsync) + '\n'
        ret = ret + 'ssh identity file: ' + str(self.ssh_identity_file) + '\n'
        ret = ret + 'use timestamp for backup dirs: ' + str(self.use_timestamp_for_backup_dir) + '\n'
        ret = ret + 'timestamp format for backup dirs: ' + str(self.timestamp_format_for_backup_dir) + '\n'
        ret = ret + 'active plugins: ' + str(self.active_plugins) + '\n'
        ret = ret + 'disk tag: ' + str(self.disk_tag) + '\n'
        ret = ret + 'disk timeout: ' + str(self.disk_timeout) + '\n'
        ret = ret + 'servers:\n'
        for inst in self._remote_servers:
            ret = ret + '  %s\n' % str(inst)
        return ret

class BackupPluginConfig(object):
    def __init__(self, 
                 backup_app, 
                 plugin_name=None,
                 retention_time=None,
                 retention_count=None
                 ):
        self.backup_app = backup_app
        self.parent = backup_app.config
        self.plugin_name = plugin_name
        self._retention_time = retention_time
        self._retention_count= retention_count

    @property
    def retention_time(self):
        if self._retention_time is None:
            return self.parent.retention_time
        else:
            return self._retention_time

    @retention_time.setter
    def retention_time(self, value):
        if value is not None:
            if isinstance(value, int):
                self._retention_time = datetime.timedelta(seconds=int(value))
            elif isinstance(value, float):
                self._retention_time = datetime.timedelta(seconds=float(value))
            elif isinstance(value, datetime.timedelta):
                self._retention_time = value
            else:
                raise ValueError('retention_time %s is invalid.' %(str(value)))
        else:
            self._retention_time = None

    @property
    def retention_count(self):
        if self._retention_count is None:
            return self.parent.retention_count
        else:
            return self._retention_count

    @retention_count.setter
    def retention_count(self, value):
        if value is not None:
            self._retention_count = int(value)
        else:
            self._retention_count = None

    @property
    def intermediate_backup_directory(self):
        ret = os.path.join(self.parent.intermediate_backup_directory, self.plugin_name)
        return ret
    
    @property
    def base_directory(self):
        return self.parent.intermediate_backup_directory
    
    def _read_conf(self, inifile):
        return True
    
    def _write_conf(self, inifile):
        return True

    def load(self):
        filename = self.parent.get_plugin_config_file(self.plugin_name)
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.retention_time = inifile.get(None, 'RetentionTime', None)
        self.retention_count = inifile.get(None, 'RetentionCount', None)
        ret = self._read_conf(inifile)
        return ret
        
    def save(self):
        filename = self.parent.get_plugin_config_file(self.plugin_name)
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config
        if self._retention_time is None:
            inifile.remove(None, 'RetentionTime')
        else:
            inifile.set(None, 'RetentionTime', self._retention_time.total_seconds())
        if self._retention_count is None:
            inifile.remove(None, 'RetentionCount')
        else:
            inifile.set(None, 'RetentionCount', self.retention_count)
        ret = self._write_conf(inifile)
        ret = inifile.save(filename)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'plugin name: ' + str(self.plugin_name) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        ret = ret + 'retention count: ' + str(self._retention_count) + '\n'
        return ret
