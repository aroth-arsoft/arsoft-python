#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import datetime
import re
from arsoft.inifile import IniFile
from arsoft.filelist import *


class RegisteredDiskList(object):
    def __init__(self, path, key='disk'):
        self.clear()
        self.path = path
        self._key = key

    def clear(self):
        self._config_items = {}
        self._disks = []
        self._last_error = None
        self._dirty = False

    def reset(self):
        ret = True
        # remove all items to make sure the config is clean
        for (filename, item) in self._config_items.iteritems():
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError as e:
                    self._last_error = str(e)
                    ret = False
            else:
                # file is already gone, which is fine
                pass
        self.clear()
        return ret

    @property
    def disks(self):
        ret = []
        for item in self._config_items.itervalues():
            value = item.get(None, self._key, default=None)
            if value:
                ret.append( value )
        return ret

    @property
    def dirty(self):
        return self._dirty

    @property
    def last_error(self):
        return self._last_error

    def open(self, config_dir=None):
        if config_dir is not None:
            self.path = config_dir
        self._last_error = None
        self._dirty = False
        try:
            self._config_items = {}
            ret = True
            files = os.listdir(self.path)
            for f in files:
                (basename, ext) = os.path.splitext(f)
                if ext == '.conf':
                    fullpath = os.path.join(self.path, f)
                    item = IniFile(filename=fullpath, commentPrefix='#', keyValueSeperator='=', disabled_values=False)
                    self._config_items[fullpath] = item
        except IOError as e:
            self._last_error = str(e)
            ret = False
        except OSError as e:
            self._last_error = str(e)
            ret = False
        return ret
    
    def save(self):
        ret = True
        if self._dirty:
            # only save the config when it's marked as dirty
            for (filename, item) in self._config_items.iteritems():
                if item.empty:
                    if os.path.exists(filename):
                        try:
                            os.remove(filename)
                        except OSError as e:
                            self._last_error = str(e)
                            ret = False
                    else:
                        # file is already gone, which is fine
                        pass
                elif not item.save():
                    ret = False
        return ret

    def register_disk(self, name, pattern):
        # first check if the pattern already exists
        found_in_file = None
        for item in self._config_items.itervalues():
            value = item.get(None, self._key, default=None)
            if value and value == pattern:
                found_in_file = item
        if not found_in_file:
            # create new config item
            filename = re.sub(r'[\s]', '_', name)
            fullpath = os.path.join(self.path, filename + '.conf')
            item = IniFile(filename=fullpath, commentPrefix='#', keyValueSeperator='=', disabled_values=False)
            item.set(None, self._key, pattern)
            self._config_items[fullpath] = item
            self._dirty = True
        return True

    def unregister_disk(self, name, pattern):
        #print('unregister_disk %s, %s' %(name, pattern))
        # first check if the pattern already exists
        ret = False
        for item in self._config_items.itervalues():
            value = item.get(None, self._key, default=None)
            if value and value == pattern:
                #print('remove ' + self._key)
                ret = item.remove(None, self._key)
                if ret:
                    #print('ini=' + item.asString())
                    self._dirty = True
                break
        return ret

class ExternalDiskManagerDefaults(object):
    CONFIG_DIR = '/etc/edskmgr'
    MAIN_CONF = 'main.conf'
    HOOK_DIR = 'hook.d'
    ADDITIONAL_CONFIG_DIR = 'conf.d'

class ExternalDiskManagerConfig(object):
    def __init__(self, config_dir=ExternalDiskManagerDefaults.CONFIG_DIR, 
                 hook_dir=ExternalDiskManagerDefaults.HOOK_DIR):
        self.config_dir = config_dir
        self.main_conf = os.path.join(config_dir, ExternalDiskManagerDefaults.MAIN_CONF)
        self.hook_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
        self.additional_config_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)
        self._internal_disks = RegisteredDiskList(self.additional_config_dir, 'INTERNAL_DISKS')
        self._external_disks = RegisteredDiskList(self.additional_config_dir, 'EXTERNAL_DISKS')

    def clear(self):
        self.config_dir = ExternalDiskManagerDefaults.CONFIG_DIR
        self.hook_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
        self.additional_config_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)

        self._config_internal_disks.load()
        self._external_disks.load()

    @property
    def internal_disks(self):
        return self._internal_disks

    @property
    def external_disks(self):
        return self._external_disks

    def open(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.config_dir = config_dir
            self.main_conf = os.path.join(config_dir, ExternalDiskManagerDefaults.MAIN_CONF)
            self.hook_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
            self.additional_config_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)

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

        # load the disk lists
        self._internal_disks.open(self.additional_config_dir)
        self._external_disks.open(self.additional_config_dir)

        return ret

    def save(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.main_conf = os.path.join(config_dir, ExternalDiskManagerDefaults.MAIN_CONF)
            self.hook_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
            self.additional_config_dir = os.path.join(config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)

        ret = True
        if not os.path.isdir(config_dir):
            try:
                os.mkdir(config_dir)
            except OSError as e:
                print(e)
                ret = False
                pass

        if not os.path.isdir(self.hook_dir):
            try:
                os.mkdir(self.hook_dir)
            except OSError as e:
                print(e)
                ret = False
                pass

        if not os.path.isdir(self.additional_config_dir):
            try:
                os.mkdir(self.additional_config_dir)
            except OSError as e:
                print(e)
                ret = False
                pass

        if not self._write_main_conf(self.main_conf):
            ret = False

        if not self._internal_disks.save():
            print(self._internal_disks.last_error)
            ret = False
        if not self._external_disks.save():
            print(self._external_disks.last_error)
            ret = False

        return ret

    def _read_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        ret = inifile.open(filename)
        return ret
        
    def _write_main_conf(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        # read existing file
        inifile.open(filename)
        # and modify it according to current config

        ret = inifile.save(filename)
        return ret
    
    def reset(self):
        self._external_disks.reset()
        self._internal_disks.reset()
        return True

    def register_disk(self, name, pattern, external=True):
        if external:
            # when register a external disk remove the same disk from the internal lists
            if self._internal_disks.unregister_disk(name, pattern):
                self._internal_disks.save()
            ret = self._external_disks.register_disk(name, pattern)
        else:
            # when register a internal disk remove the same disk from the external lists
            if self._external_disks.unregister_disk(name, pattern):
                self._external_disks.save()
            ret = self._internal_disks.register_disk(name, pattern)
        return True
        
    def unregister_disk(self, name, pattern, external=True):
        if external:
            ret = self._external_disks.unregister_disk(name, pattern)
        else:
            ret = self._internal_disks.unregister_disk(name, pattern)
        return True

    def __str__(self):
        ret = ''
        ret = ret + 'config_dir: ' + str(self.config_dir) + '\n'
        ret = ret + 'hook directory: ' + str(self.hook_dir) + '\n'
        ret = ret + 'add. config directory: ' + str(self.additional_config_dir) + '\n'
        return ret
 
