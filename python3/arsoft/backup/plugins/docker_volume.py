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
            self.compress = False
            self.compress_format = 'bzip2'
            self.inifile = inifile
            self.section = section

        def read_conf(self):
            self._volume_list = self.inifile.getAsArray(self.section, 'Volume', [])
            self.compress = self.inifile.getAsBoolean(None, 'compress', False)
            self.compress_format = self.inifile.get(None, 'compress_format', 'bzip2')
            return True

        def write_conf(self, inifile):
            if self._volume_list:
                inifile.set(self.section, 'Volume', self._volume_list.items)
            else:
                inifile.set(self.section, 'Volume', [])
            inifile.set(self.section, 'compress', self.compress)
            inifile.set(self.section, 'compress_format', self.compress_format)
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

                    if item.compress:
                        tar_compress = ''
                        if item.compress_format == 'bzip2':
                            volume_bak_file = volume + '.tar.bz2'
                            tar_compress = '-j'
                        elif item.compress_format == 'gzip':
                            volume_bak_file = volume + '.tar.gz'
                            tar_compress = '-z'
                        elif item.compress_format == 'xz':
                            volume_bak_file = volume + '.tar.xz'
                            tar_compress = '-J'
                        backup_dest_file = os.path.join(backup_dir, volume_bak_file)
                        self.writelog('volume %s compress to %s' % (volume, backup_dest_file))
                        args = ['/usr/bin/docker', 'run', '--rm', '-v', '%s:/data' % volume, '-v', '%s:/dest' % backup_dir, 
                            'busybox', 
                            'tar', 'c', tar_compress, '-f', '/dest/%s' % volume_bak_file, '-C', '/data', './' ]
                    else:
                        backup_dest_file = os.path.join(backup_dir, volume)
                        try:
                            if not os.path.isdir(backup_dest_file):
                                os.makedirs(backup_dest_file)
                        except OSError as e:
                            self.writelog('Unable to create directory %s for docker volume %s, error %s.\n' % (backup_dest_file, volume, e))
                            backup_dest_file = None

                        self.writelog('volume %s copy to %s' % (volume, backup_dest_file))
                        args = ['/usr/bin/docker', 'run', '--rm', '-v', '%s:/data' % volume, '-v', '%s:/dest/data' % backup_dest_file, 
                            'busybox', 
                            'cp', '-a', '/data', '/dest/' ]
                    if backup_dest_file:
                        (sts, stdout_data, stderr_data) = runcmdAndGetData(executable='/usr/bin/docker', args=args, shell=False, 
                            verbose=True, outputStdErr=True, outputStdOut=True)
                        if sts == 0:
                            dir_backup_filelist.append(backup_dest_file)
            self.backup_app.append_to_filelist(dir_backup_filelist)

        return ret

