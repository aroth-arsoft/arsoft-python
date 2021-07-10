#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ..plugin import *
from arsoft.filelist import *
from arsoft.rsync import Rsync
from arsoft.utils import runcmdAndGetData

class DockerVolumeBackupPluginConfig(BackupPluginConfig):
    
    class DockerVolumeConfigItem(object):
        def __init__(self, inifile=None, section=None):
            self._volume_list = None
            self.inifile = inifile
            self.section = section

        def read_conf(self):
            self._volume_list = self.inifile.getAsArray(self.section, 'Volume', [])
            return True

        def write_conf(self, inifile):
            if self._volume_list:
                inifile.set(self.section, 'Volume', self._volume_list.items)
            else:
                inifile.set(self.section, 'Volume', [])
            return True

        @property
        def volume_list(self):
            return self._volume_list

        @volume_list.setter
        def volume_list(self, value):
            if value is not None:
                self._volume_list = value
            else:
                self._volume_list = None

        def __str__(self):
            if self._volume_list is None:
                return 'None'
            else:
                return '%s' % (self._volume_list)

    def __init__(self, parent):
        BackupPluginConfig.__init__(self, parent, 'docker_volume')
        self._items = []

    @property
    def items(self):
        return self._items

    def _read_conf(self, inifile):
        ret = True
        for section in inifile.sections:
            item = DockerVolumeBackupPluginConfig.DockerVolumeConfigItem(inifile, section)
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

class DockerVolumeBackupPlugin(BackupPlugin):
    def __init__(self, backup_app):
        self.config = DockerVolumeBackupPluginConfig(backup_app)
        BackupPlugin.__init__(self, backup_app, 'docker_volume')

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
                for volume in item.volume_list:
                    volume_bak_file = volume + '.tar.bzip2'
                    backup_dest_file = os.path.join(backup_dir, volume_bak_file)
                    print('volume %s -> %s' % (volume, backup_dest_file))

                    args = ['/usr/bin/docker', 'run', '--rm', '-v', '%s:/data' % volume, '-v', '%s:/dest' % backup_dir, 
                        'busybox', 
                        'tar', 'c', '-j', '-f', '/dest/%s' % volume_bak_file, '-C', '/data', './' ]

                    (sts, stdout_data, stderr_data) = runcmdAndGetData(executable='/usr/bin/docker', args=args, shell=False, 
                        verbose=True, outputStdErr=True, outputStdOut=True)
                    if sts == 0:
                        dir_backup_filelist.append(backup_dest_file)
            self.backup_app.append_to_filelist(dir_backup_filelist)

        return ret

