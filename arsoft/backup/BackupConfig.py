#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import datetime
from FileList import *

class BackupConfig(object):
    
    DEFAULT_FILESYSTEM = 'ext4'
    DEFAULT_RETENTION_TIME_S = 86400 * 7
    DEFAULT_BACKUP_DIR = None
    DEFAULT_RESTORE_DIR = None

    def __init__(self, filename='/etc/default/backup', 
                 retention_time=BackupConfig.DEFAULT_RETENTION_TIME_S, 
                 backup_directory=BackupConfig.DEFAULT_BACKUP_DIR, 
                 restore_directory=BackupConfig.DEFAULT_RESTORE_DIR, 
                 filesystem=BackupConfig.DEFAULT_FILESYSTEM, 
                 filelist_include=None, 
                 filelist_exclude=None):
        self.filename = filename
        self.filesystem = filesystem
        self.retention_time = retention_time
        self.backup_directory = backup_directory
        if filelist_exclude is not None:
            if isinstance(filelist_exclude, FileList):
                self.filelist_exclude = filelist_exclude
            else:
                self.filelist_exclude = FileList(filelist_exclude)
        else:
            self.filelist_exclude = None

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

    def open(self, filename=None):
        if filename is None:
            filename = self.filename

        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        self.filesystem = inifile.get(None, 'Filesystem', BackupConfig.DEFAULT_FILESYSTEM)
        self.retention_time = inifile.get(None, 'RetentionTime', BackupConfig.DEFAULT_RETENTION_TIME_S)
        self.backup_directory = inifile.get(None, 'BackupDirectory', BackupConfig.DEFAULT_BACKUP_DIR)
        self.restore_directory = inifile.get(None, 'RestoreDirectory', BackupConfig.DEFAULT_RESTORE_DIR)
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.filename

        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.set(None, 'Filesystem', self.filesystem)
        inifile.set(None, 'RetentionTime', self.retention_time)
        inifile.set(None, 'BackupDirectory', self.backup_directory)
        inifile.set(None, 'RestoreDirectory', self.restore_directory)
        ret = inifile.save(filename)
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'filesystem: ' + str(self.filesystem) + '\n'
        ret = ret + 'backup directory: ' + str(self.backup_directory) + '\n'
        ret = ret + 'retention time: ' + str(self._retention_time) + '\n'
        ret = ret + 'include file list: ' + str(self._filelist_include) + '\n'
        ret = ret + 'exclude file list: ' + str(self._filelist_exclude) + '\n'
