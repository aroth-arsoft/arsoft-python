#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.trac.admin import TracAdmin

import tempfile
import sys

class TracBackupPluginConfig(BackupPluginConfig):

    class TracEnvItem(object):
        def __init__(self, path, include_database=False):
            self.path = path
            self.include_database = include_database

        def __str__(self):
            return '%s' % (self.path)

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'trac')
        self._instance_list = []

    @property
    def instance_list(self):
        return self._instance_list

    @instance_list.setter
    def instance_list(self, value):
        self._instance_list = value

    def _read_conf(self, inifile):
        for sect in inifile.sections:
            tracenv = inifile.get(sect, 'tracenv', None)
            include_database = inifile.getAsBoolean(sect, 'include_database', False)
            if tracenv:
                self._instance_list.append(TracBackupPluginConfig.TracEnvItem(tracenv, include_database))
        return True
    
    def _write_conf(self, inifile):
        return True

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        ret = ret + 'instances:\n'
        if self._instance_list:
            for item in self._instance_list:
                ret = ret + '  %s:\n' % item.path
        return ret

class TracBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = TracBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'trac')

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            trac_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for item in self.config.instance_list:
                if self.backup_app._verbose:
                    print('backup %s' % str(item))

                trac_admin = TracAdmin(item.path, verbose=self.backup_app._verbose)
                tmp_backup_dir = tempfile.TemporaryDirectory(dir=backup_dir)
                if not trac_admin.hotcopy(tmp_backup_dir.name, include_database=item.include_database):
                    sys.stderr.write('Failed to create hot copy of %s. %s\n' % (str(item), trac_admin.last_error))
                    ret = False

            #print(trac_backup_filelist)
            self.backup_app.append_to_filelist(trac_backup_filelist)
            #print(self.intermediate_filelist)
        return ret
 
