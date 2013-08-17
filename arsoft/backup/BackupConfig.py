#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import datetime
from arsoft.inifile import IniFile
from FileList import *

class BackupConfigDefaults(object):
    CONFIG_DIR = '/etc/arsoft-backup'
    MAIN_CONF = 'main.conf'
    CONFIG_FILE_EXTENSTION = '.conf'
    INCLUDE_DIR = 'include.d'
    EXCLUDE_DIR = 'exclude.d'
    FILESYSTEM = 'ext4'
    RETENTION_TIME_S = 86400 * 7
    BACKUP_DIR = None
    RESTORE_DIR = None
    INTERMEDIATE_BACKUP_DIR = None
    EJECT_UNUSED_BACKUP_DISCS = True
    USE_FILESYSTEM_SNAPSHOTS = False
    USE_SSH_FOR_RSYNC = True
    SSH_IDENTITY_FILE = None
    USE_TIMESTAMP_FOR_BACKUP_DIR = True
    TIMESTAMP_FORMAT_FOR_BACKUP_DIR = '%Y%m%d%H%M%S'
    ACTIVE_PLUGINS = ['git', 'dir']

class BackupConfig(object):
    def __init__(self, config_dir=BackupConfigDefaults.CONFIG_DIR, 
                 retention_time=BackupConfigDefaults.RETENTION_TIME_S, 
                 backup_directory=BackupConfigDefaults.BACKUP_DIR, 
                 restore_directory=BackupConfigDefaults.RESTORE_DIR, 
                 intermediate_backup_directory=BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR, 
                 filesystem=BackupConfigDefaults.FILESYSTEM,
                 filelist_include_dir=BackupConfigDefaults.INCLUDE_DIR,
                 filelist_exclude_dir=BackupConfigDefaults.EXCLUDE_DIR,
                 eject_unused_backup_discs=BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS,
                 use_filesystem_snapshots=BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS,
                 use_ssh_for_rsync=BackupConfigDefaults.USE_SSH_FOR_RSYNC,
                 ssh_identity_file=BackupConfigDefaults.SSH_IDENTITY_FILE,
                 use_timestamp_for_backup_dir=BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR,
                 timestamp_format_for_backup_dir=BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR,
                 active_plugins=BackupConfigDefaults.ACTIVE_PLUGINS,
                 filelist_include=None, 
                 filelist_exclude=None):
        self.config_dir = config_dir
        self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
        self.filesystem = filesystem
        self.retention_time = retention_time
        self.backup_directory = backup_directory
        self.intermediate_backup_directory = intermediate_backup_directory
        self.filelist_include = filelist_include
        self.filelist_exclude = filelist_exclude
        self.filelist_include_dir = filelist_include_dir
        self.filelist_exclude_dir = filelist_exclude_dir
        self.eject_unused_backup_discs = eject_unused_backup_discs
        self.use_filesystem_snapshots = use_filesystem_snapshots
        self.use_ssh_for_rsync = use_ssh_for_rsync
        self.ssh_identity_file = ssh_identity_file
        self.use_timestamp_for_backup_dir = use_timestamp_for_backup_dir
        self.timestamp_format_for_backup_dir = timestamp_format_for_backup_dir
        self.active_plugins = active_plugins

    def clear(self):
        self.config_dir = BackupConfigDefaults.CONFIG_DIR
        self.filesystem = BackupConfigDefaults.FILESYSTEM
        self.retention_time = BackupConfigDefaults.RETENTION_TIME_S
        self.backup_directory = BackupConfigDefaults.BACKUP_DIR
        self.intermediate_backup_directory = BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR
        self.filelist_include = None
        self.filelist_exclude = None
        self.filelist_include_dir = BackupConfigDefaults.INCLUDE_DIR
        self.filelist_exclude_dir = BackupConfigDefaults.EXCLUDE_DIR
        self.eject_unused_backup_discs = BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS
        self.use_filesystem_snapshots = BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS
        self.use_ssh_for_rsync = BackupConfigDefaults.USE_SSH_FOR_RSYNC
        self.ssh_identity_file = BackupConfigDefaults.SSH_IDENTITY_FILE
        self.use_timestamp_for_backup_dir = BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR
        self.timestamp_format_for_backup_dir = BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR
        self.active_plugins = BackupConfigDefaults.ACTIVE_PLUGINS

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

    def open(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)
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

        filelist_path = os.path.join(config_dir, self.filelist_include_dir)
        if not os.path.isdir(filelist_path):
            try:
                os.mkdir(filelist_path)
            except OSError:
                pass

        # reload the file lists
        self.filelist_include = self.filelist_exclude_dir
        self.filelist_exclude = self.filelist_exclude_dir

        return ret

    def save(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)

        ret = self._write_main_conf(self.main_conf)

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

    def _read_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.filesystem = inifile.get(None, 'Filesystem', BackupConfigDefaults.FILESYSTEM)
        self.retention_time = datetime.timedelta(seconds=float(inifile.get(None, 'RetentionTime', BackupConfigDefaults.RETENTION_TIME_S)))
        self.backup_directory = inifile.get(None, 'BackupDirectory', BackupConfigDefaults.BACKUP_DIR)
        self.restore_directory = inifile.get(None, 'RestoreDirectory', BackupConfigDefaults.RESTORE_DIR)
        self.intermediate_backup_directory = inifile.get(None, 'IntermediateBackupDirectory', BackupConfigDefaults.INTERMEDIATE_BACKUP_DIR)
        self.eject_unused_backup_discs = inifile.getAsBoolean(None, 'EjectUnusedBackupDiscs', BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS)
        self.use_filesystem_snapshots = inifile.getAsBoolean(None, 'UseFilesystemSnapshots', BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS)
        self.use_ssh_for_rsync = inifile.getAsBoolean(None, 'UseSSHForRsync', BackupConfigDefaults.USE_SSH_FOR_RSYNC)
        self.ssh_identity_file = inifile.get(None, 'SSHIdentityFile', BackupConfigDefaults.SSH_IDENTITY_FILE)
        self.use_timestamp_for_backup_dir = inifile.getAsBoolean(None, 'UseTimestampForBackupDir', BackupConfigDefaults.USE_TIMESTAMP_FOR_BACKUP_DIR)
        self.timestamp_format_for_backup_dir = inifile.get(None, 'TimestampFormatForBackupDir', BackupConfigDefaults.TIMESTAMP_FORMAT_FOR_BACKUP_DIR)
        self.filelist_include_dir = inifile.get(None, 'FileListIncludeDirectory', BackupConfigDefaults.INCLUDE_DIR)
        self.filelist_exclude_dir = inifile.get(None, 'FileListExcludeDirectory', BackupConfigDefaults.EXCLUDE_DIR)
        self.active_plugins = inifile.getAsArray(None, 'ActivePlugins', BackupConfigDefaults.ACTIVE_PLUGINS)
        return ret
        
    def _write_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config
        inifile.set(None, 'Filesystem', self.filesystem)
        inifile.set(None, 'RetentionTime', self.retention_time.total_seconds())
        inifile.set(None, 'BackupDirectory', self.backup_directory)
        inifile.set(None, 'RestoreDirectory', self.restore_directory)
        inifile.set(None, 'IntermediateBackupDirectory', self.intermediate_backup_directory)
        inifile.setAsBoolean(None, 'EjectUnusedBackupDiscs', self.eject_unused_backup_discs)
        inifile.setAsBoolean(None, 'UseFilesystemSnapshots', self.use_filesystem_snapshots)
        inifile.setAsBoolean(None, 'UseSSHForRsync', self.use_ssh_for_rsync)
        inifile.set(None, 'SSHIdentityFile', self.ssh_identity_file)
        inifile.setAsBoolean(None, 'UseTimestampForBackupDir', self.use_timestamp_for_backup_dir)
        inifile.set(None, 'TimestampFormatForBackupDir', self.timestamp_format_for_backup_dir)
        inifile.set(None, 'FileListIncludeDirectory', self.filelist_include_dir)
        inifile.set(None, 'FileListExcludeDirectory', self.filelist_exclude_dir)
        inifile.set(None, 'ActivePlugins', self.active_plugins)

        ret = inifile.save(filename)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'filesystem: ' + str(self.filesystem) + '\n'
        ret = ret + 'backup directory: ' + str(self.backup_directory) + '\n'
        ret = ret + 'restore directory: ' + str(self.restore_directory) + '\n'
        ret = ret + 'intermediate backup directory: ' + str(self.intermediate_backup_directory) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        ret = ret + 'include file list: ' + str(self._filelist_include) + '\n'
        ret = ret + 'exclude file list: ' + str(self._filelist_exclude) + '\n'
        ret = ret + 'eject unused backup discs: ' + str(self.eject_unused_backup_discs) + '\n'
        ret = ret + 'use filesystem snapshots: ' + str(self.use_filesystem_snapshots) + '\n'
        ret = ret + 'use ssh for rsync: ' + str(self.use_ssh_for_rsync) + '\n'
        ret = ret + 'ssh identity file: ' + str(self.ssh_identity_file) + '\n'
        ret = ret + 'use timestamp for backup dirs: ' + str(self.use_timestamp_for_backup_dir) + '\n'
        ret = ret + 'timestamp format for backup dirs: ' + str(self.timestamp_format_for_backup_dir) + '\n'
        ret = ret + 'active plugins: ' + str(self.active_plugins) + '\n'
        return ret

class BackupPluginConfig(object):
    def __init__(self, 
                 backup_app, 
                 plugin_name=None,
                 retention_time=None 
                 ):
        self.backup_app = backup_app
        self.parent = backup_app.config
        self.plugin_name = plugin_name
        self._retention_time = retention_time

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
    def intermediate_backup_directory(self):
        ret = self.parent.intermediate_backup_directory
        if ret is None:
            ret = self.parent.backup_directory
        ret = os.path.join(ret, self.plugin_name)
        return ret
    
    @property
    def base_directory(self):
        ret = self.parent.intermediate_backup_directory
        if ret is None:
            ret = self.parent.backup_directory
        return ret
    
    def _read_conf(self, inifile):
        return True
    
    def _write_conf(self, inifile):
        return True

    def load(self):
        filename = self.parent.get_plugin_config_file(self.plugin_name)
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.retention_time = datetime.timedelta(seconds=float(inifile.get(None, 'RetentionTime', BackupConfigDefaults.RETENTION_TIME_S)))
        ret = self._read_conf(inifile)
        return ret
        
    def save(self):
        filename = self.parent.get_plugin_config_file(self.plugin_name)
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config
        inifile.set(None, 'RetentionTime', self.retention_time.total_seconds())
        ret = self._write_conf(inifile)
        ret = inifile.save(filename)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'plugin name: ' + str(self.plugin_name) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        return ret
