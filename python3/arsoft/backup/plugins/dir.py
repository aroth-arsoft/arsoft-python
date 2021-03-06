#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.rsync import Rsync

class DirectoryBackupPluginConfig(BackupPluginConfig):
    
    class DirectoryConfigItem(object):
        def __init__(self, inifile=None, section=None):
            self._directory_list = None
            self._exclude_list = None
            self.inifile = inifile
            self.section = section

        def read_conf(self):
            self.directory_list = self.inifile.getAsArray(self.section, 'Directories', [])
            self.exclude_list = self.inifile.getAsArray(self.section, 'Exclude', [])
            return True

        def write_conf(self, inifile):
            if self._directory_list:
                inifile.set(self.section, 'Directories', self._directory_list.items)
            else:
                inifile.set(self.section, 'Directories', [])
            if self._exclude_list:
                inifile.set(self.section, 'Exclude', self._exclude_list.items)
            else:
                inifile.set(self.section, 'Exclude', [])
            return True

        @property
        def directory_list(self):
            return self._directory_list

        @directory_list.setter
        def directory_list(self, value):
            if value is not None:
                if isinstance(value, FileListWithDestination):
                    self._directory_list = value
                else:
                    self._directory_list = FileListWithDestination.from_list(value, use_glob=False)
            else:
                self._directory_list = None

        @property
        def exclude_list(self):
            return self._exclude_list

        @exclude_list.setter
        def exclude_list(self, value):
            #print('exclude_list=%s' % (value))
            if value is not None:
                if isinstance(value, FileList):
                    self._exclude_list = value
                else:
                    self._exclude_list = FileList.from_list(value, use_glob=False)
            else:
                self._exclude_list = None
            #print('_exclude_list=%s' % (self._exclude_list))

        def __str__(self):
            if self._directory_list is None:
                return 'None'
            if self._exclude_list is None:
                return str(self.directory_list)
            else:
                return '%s (exclude %s)' % (self.directory_list, self._exclude_list)

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'dir')
        self._items = []

    @property
    def items(self):
        return self._items

    def _read_conf(self, inifile):
        ret = True
        for section in inifile.sections:
            item = DirectoryBackupPluginConfig.DirectoryConfigItem(inifile, section)
            if item.read_conf():
                self._items.append(item)
            else:
                ret = False
        return ret

    def _write_conf(self, inifile):
        ret = True
        for item in self._items:
            if not item.write_conf(inifile):
                ret = False
        return ret

    def __str__(self):
        ret = BackupPluginConfig.__str__(self)
        for item in self._items:
            ret = ret + ' item %s\n' % str(item)
        return ret

class DirectoryBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = DirectoryBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'dir')

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            self.writelog('Failed to create directory %s' % backup_dir)
            ret = False
        if ret:
            my_stdout = self.logfile_proxy
            dir_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for item in self.config.items:
                item_exclude_list = item.exclude_list
                for (source_dir, dest_dir) in item.directory_list:
                    backup_dest_dir = os.path.join(backup_dir, dest_dir)
                    if os.path.isdir(source_dir):
                        if backup_dest_dir[-1] != '/':
                            backup_dest_dir += '/'
                        if self.backup_app._verbose:
                            print('backup %s to %s' % (source_dir, backup_dest_dir))
                        if Rsync.sync_directories(source_dir, backup_dest_dir, exclude=item_exclude_list, stdout=my_stdout, stderr_to_stdout=True, verbose=self.backup_app.verbose):
                            dir_backup_filelist.append(backup_dest_dir)
                    elif os.path.isfile(source_dir):
                        backup_dest_dir = os.path.join(backup_dest_dir, os.path.basename(source_dir))
                        if self.backup_app._verbose:
                            print('backup %s to %s' % (source_dir, backup_dest_dir))
                        if Rsync.sync_file(source_dir, backup_dest_dir, exclude=item_exclude_list, stdout=my_stdout, stderr_to_stdout=True, verbose=self.backup_app.verbose):
                            dir_backup_filelist.append(backup_dest_dir)
                    elif os.path.exists(source_dir):
                        self.writelog('Refuse to back up %s because it is not a file or directory.\n' % source_dir)
                        ret = False
                    else:
                        self.writelog('Refuse to back up %s because it is not exist.\n' % source_dir)
                        ret = False
            self.backup_app.append_to_filelist(dir_backup_filelist)

        return ret

