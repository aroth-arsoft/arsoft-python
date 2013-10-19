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
            self.inifile = inifile
            self.section = section

        def read_conf(self):
            self.directory_list = self.inifile.getAsArray(self.section, 'Directories', [])
            return True

        def write_conf(self, inifile):
            if self._directory_list:
                inifile.set(self.section, 'Directories', self._directory_list.items)
            else:
                inifile.set(self.section, 'Directories', [])
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

class DirectoryBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = DirectoryBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'dir')

    def perform_backup(self, **kwargs):
        ret = True
        backup_dir = self.config.intermediate_backup_directory
        if not self._mkdir(backup_dir):
            ret = False
        if ret:
            dir_backup_filelist = FileListItem(base_directory=self.config.base_directory)
            for item in self.config.items:
                for (source_dir, dest_dir) in item.directory_list:
                    backup_dest_dir = os.path.join(backup_dir, dest_dir)
                    if os.path.isdir(source_dir):
                        if backup_dest_dir[-1] != '/':
                            backup_dest_dir += '/'
                        if self.backup_app._verbose:
                            print('backup %s to %s' % (source_dir, backup_dest_dir))
                        if Rsync.sync_directories(source_dir, backup_dest_dir):
                            dir_backup_filelist.append(backup_dest_dir)
                    elif os.path.isfile(source_dir):
                        backup_dest_dir = os.path.join(backup_dest_dir, os.path.basename(source_dir))
                        if self.backup_app._verbose:
                            print('backup %s to %s' % (source_dir, backup_dest_dir))
                        if Rsync.sync_file(source_dir, backup_dest_dir):
                            dir_backup_filelist.append(backup_dest_dir)
                    else:
                        sys.stderr.write('Refuse to back up %s because it is not a file or directory.\n' % source_dir)
            self.backup_app.append_to_filelist(dir_backup_filelist)

        return ret

