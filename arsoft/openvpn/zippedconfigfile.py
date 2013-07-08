#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import sys
from arsoft.zipfileutils import ZipFileEx
from configfile import ConfigFile
from systemconfig import SystemConfig
import arsoft.utils
import zipfile

class ZippedConfigFile(object):

    def __init__(self, filename=None, mode='r'):
        self.filename = filename
        self.mode = mode
        self._zip = None
        self._config_file_info = None
        self.last_error = None
        
    def _ensure_open(self):
        if self._zip is None:
            ret = self.open()
        else:
            ret = True
        return ret

    def open(self, filename=None, mode=None):
        if filename is None:
            filename = self.filename
        if mode is None:
            mode = self.mode

        self._zip = ZipFileEx(filename, mode)
        ret = True if self._zip else False
        return ret

    @staticmethod
    def is_zip_config_file(filename, mode='r'):
        try:
            fobj = ZipFileEx(filename, mode)
            if fobj:
                config_file_info = None
                fileinfolist = fobj.infolist()
                for fileinfo in fileinfolist:
                    (basename, ext) = os.path.splitext(fileinfo.filename)
                    if ext == '.ovpn' or ext == '.conf':
                        config_file_info = fileinfo
                        break
                ret = True if config_file_info else False
            else:
                ret = False
        except zipfile.BadZipfile as e:
            ret = False
        return ret

    @property
    def valid(self):
        ret = self._find_config_file()
        return ret

    def close(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None
        self._config_file_info = None
    
    def _find_config_file(self):
        if self._config_file_info is None:
            if self._ensure_open():
                fileinfolist = self._zip.infolist()
                for fileinfo in fileinfolist:
                    (basename, ext) = os.path.splitext(fileinfo.filename)
                    if ext == '.ovpn' or ext == '.conf':
                        self._config_file_info = fileinfo
                        break
        return True if self._config_file_info is not None else False
    
    def _find_file(self, filename):
        ret = None
        if self._ensure_open():
            fileinfolist = self._zip.infolist()
            for fileinfo in fileinfolist:
                if fileinfo.filename == filename:
                    ret = fileinfo
                    break
        return ret

    @property
    def name(self):
        cfgfile = self.config_file
        if cfgfile is not None:
            return cfgfile.name
        else:
            return None

    @property
    def config_filename(self):
        self._find_config_file()
        return self._config_file_info.filename if self._config_file_info else None

    @property
    def config_file(self):
        self._find_config_file()
        fp = self._zip.open(self._config_file_info.filename, self.mode) if self._config_file_info else None
        ret = ConfigFile(fp, zipfile=self) if fp else None
        return ret
    
    def extractall(self, target_directory):
        if self._ensure_open():
            self._zip.extractall(target_directory)
            ret = True
        else:
            ret = False
        return ret

    def __getitem__(self, name):
        fileinfo = self._find_file(name)
        return self._zip.open(fileinfo.filename, self.mode) if fileinfo else None
    
    def __iter__(self):
        if self._ensure_open():
            return iter(self._zip)
        else:
            return None
        
    def extract(self, name, target_directory):
        if self._ensure_open():
            self._zip.extract(name, target_directory)
            ret = True
        else:
            ret = False
        return ret

    def install(self, autoStart=True, config_directory=None, root_directory=None):
        if config_directory is None:
            config_directory = '/etc/openvpn'
        if root_directory is None:
            target_config_directory = config_directory
        else:
            target_config_directory = root_directory + config_directory
        target_config_file = os.path.join(target_config_directory, self.name + '.conf')
        
        cfgfile = self.config_file
        ret = True if cfgfile else False
        if ret:
            ret = cfgfile.save(target_config_file)
        if ret and cfgfile.cert_filename:
            ret = self.extract(cfgfile.cert_filename, target_config_directory)
        if ret and cfgfile.key_filename:
            ret = self.extract(cfgfile.key_filename, target_config_directory)
        if ret and cfgfile.ca_filename:
            ret = self.extract(cfgfile.ca_filename, target_config_directory)
        if ret and cfgfile.dh_filename:
            ret = self.extract(cfgfile.dh_filename, target_config_directory)
        if ret and cfgfile.crl_filename:
            ret = self.extract(cfgfile.crl_filename, target_config_directory)

        if ret:
            print('update syscofn')
            syscfg = SystemConfig(root_directory=root_directory)
            new_autostart = syscfg.autostart
            if autoStart:
                print('add %s' % self.name)
                new_autostart.add(self.name)
            else:
                print('remove %s' % self.name)
                new_autostart.remove(self.name)
            syscfg.autostart = new_autostart
            print(syscfg.autostart)
            ret = syscfg.save()
        return ret
if __name__ == '__main__':
    c = ZippedConfigFile(sys.argv[1])

    print(c)
    print(c.config_file)
    print(c.config_file.ca_file)
    print(c[c.config_file.ca_file])
    print(iter(c))
    for f in iter(c):
        print(f.name)
