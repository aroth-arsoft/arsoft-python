#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import datetime
from arsoft.inifile import IniFile
from FileList import *

class BackupConfigDefaults(object):
    CONFIG_DIR = '/etc/arsoft-backup'
    MAIN_CONF = 'main.conf'
    INCLUDE_DIR = 'include.d'
    EXCLUDE_DIR = 'exclude.d'
    FILESYSTEM = 'ext4'
    RETENTION_TIME_S = 86400 * 7
    BACKUP_DIR = None
    RESTORE_DIR = None
    EJECT_UNUSED_BACKUP_DISCS = True
    USE_FILESYSTEM_SNAPSHOTS = False

class BackupConfig(object):
    def __init__(self, config_dir=BackupConfigDefaults.CONFIG_DIR, 
                 retention_time=BackupConfigDefaults.RETENTION_TIME_S, 
                 backup_directory=BackupConfigDefaults.BACKUP_DIR, 
                 restore_directory=BackupConfigDefaults.RESTORE_DIR, 
                 filesystem=BackupConfigDefaults.FILESYSTEM,
                 eject_unused_backup_discs=BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS,
                 use_filesystem_snapshots=BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS,
                 filelist_include=None, 
                 filelist_exclude=None):
        self.config_dir = config_dir
        self.filesystem = filesystem
        self.retention_time = retention_time
        self.backup_directory = backup_directory
        self.filelist_include = filelist_include
        self.filelist_exclude = filelist_exclude
        self.eject_unused_backup_discs = eject_unused_backup_discs
        self.use_filesystem_snapshots = use_filesystem_snapshots

    def clear(self):
        self.config_dir = BackupConfigDefaults.CONFIG_DIR
        self.filesystem = BackupConfigDefaults.FILESYSTEM
        self.retention_time = BackupConfigDefaults.RETENTION_TIME_S
        self.backup_directory = BackupConfigDefaults.BACKUP_DIR
        self.filelist_include = None
        self.filelist_exclude = None
        self.eject_unused_backup_discs = BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS
        self.use_filesystem_snapshots = BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS

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
                self._filelist_include = FileList(value)
        else:
            self._filelist_include = None

    @filelist_exclude.setter
    def filelist_exclude(self, value):
        if value is not None:
            if isinstance(value, FileList):
                self._filelist_exclude = value
            else:
                self._filelist_exclude = FileList(value)
        else:
            self._filelist_exclude = None

    def open(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
            
        main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)

        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(main_conf)
        self.filesystem = inifile.get(None, 'Filesystem', BackupConfigDefaults.FILESYSTEM)
        self.retention_time = inifile.get(None, 'RetentionTime', BackupConfigDefaults.RETENTION_TIME_S)
        self.backup_directory = inifile.get(None, 'BackupDirectory', BackupConfigDefaults.BACKUP_DIR)
        self.restore_directory = inifile.get(None, 'RestoreDirectory', BackupConfigDefaults.RESTORE_DIR)
        self.eject_unused_backup_discs = inifile.getAsBoolean(None, 'EjectUnusedBackupDiscs', BackupConfigDefaults.EJECT_UNUSED_BACKUP_DISCS)
        self.use_filesystem_snapshots = inifile.getAsBoolean(None, 'UseFilesystemSnapshots', BackupConfigDefaults.USE_FILESYSTEM_SNAPSHOTS)
        
        filelist_path = os.path.join(config_dir, BackupConfigDefaults.INCLUDE_DIR)
        self.filelist_include = FileList(filelist_path)

        filelist_path = os.path.join(config_dir, BackupConfigDefaults.EXCLUDE_DIR)
        self.filelist_exclude = FileList(filelist_path)

        return ret

    def save(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir

        main_conf = os.path.join(config_dir, BackupConfigDefaults.MAIN_CONF)

        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(main_conf)
        # and modify it according to current config
        inifile.set(None, 'Filesystem', self.filesystem)
        inifile.set(None, 'RetentionTime', self.retention_time)
        inifile.set(None, 'BackupDirectory', self.backup_directory)
        inifile.set(None, 'RestoreDirectory', self.restore_directory)
        inifile.setAsBoolean(None, 'EjectUnusedBackupDiscs', self.eject_unused_backup_discs)
        inifile.setAsBoolean(None, 'UseFilesystemSnapshots', self.use_filesystem_snapshots)
        ret = inifile.save(main_conf)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'filesystem: ' + str(self.filesystem) + '\n'
        ret = ret + 'backup directory: ' + str(self.backup_directory) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        ret = ret + 'include file list: ' + str(self._filelist_include) + '\n'
        ret = ret + 'exclude file list: ' + str(self._filelist_exclude) + '\n'
        ret = ret + 'eject unused backup discs: ' + str(self.eject_unused_backup_discs) + '\n'
        ret = ret + 'use filesystem snapshots: ' + str(self.use_filesystem_snapshots) + '\n'
        return ret
