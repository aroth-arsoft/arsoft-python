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
    
class ExternalDiskManagerConfigItem(object):
    def __init__(self, filename=None):
        self.filename = filename
        self.pattern = None
        self.external = False
        self.tags = []
        if self.filename is not None:
            self._read_conf()

    def _read_conf(self):
        inifile = IniFile(filename=self.filename, commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        self.pattern = inifile.get(None, 'Pattern', None)
        self.tags = inifile.getAsArray(None, 'Tags', [])
        self.external = inifile.getAsBoolean(None, 'External', False)

    def _write_conf(self, filename=None):
        if filename is None:
            filename = self.filename
        inifile = IniFile(filename=filename, commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.set(None, 'Pattern', self.pattern)
        inifile.set(None, 'Tags', self.tags)
        inifile.setAsBoolean(None, 'External', self.external)
        return inifile.save()

    def save(self, filename=None):
        return self._write_conf(filename)

    @property
    def is_valid(self):
        return False if self.pattern is None else True

    def remove(self):
        try:
            os.remove(self.filename)
            ret = True
        except (OSError, IOError) as e:
            print(e)
            ret = False
        return ret

    def __str__(self):
        ret = 'ExternalDiskManagerConfigItem(%s; pattern=%s; ext=%s; tags=%s)' % (self.filename, self.pattern, self.external, ','.join(self.tags))
        return ret

class ExternalDiskManagerConfig(object):
    def __init__(self, config_dir=ExternalDiskManagerDefaults.CONFIG_DIR, 
                 hook_dir=ExternalDiskManagerDefaults.HOOK_DIR):
        self.config_dir = os.path.abspath(config_dir)
        self.main_conf = os.path.join(self.config_dir, ExternalDiskManagerDefaults.MAIN_CONF)
        self.hook_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
        self.additional_config_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)
        self._items = []

    def clear(self):
        self.config_dir = ExternalDiskManagerDefaults.CONFIG_DIR
        self.hook_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
        self.additional_config_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)
        self._items = []

    @property
    def internal_disks(self):
        ret = []
        for item in self._items:
            if not item.external:
                ret.append(item.pattern)
        return ret

    @property
    def external_disks(self):
        ret = []
        for item in self._items:
            if item.external:
                ret.append(item.pattern)
        return ret
    
    @property
    def disks(self):
        ret = []
        for item in self._items:
            ret.append(item.pattern)
        return ret

    def open(self, config_dir=None):
        if config_dir is None:
            config_dir = self.config_dir
        else:
            self.config_dir = os.path.abspath(config_dir)
            self.main_conf = os.path.join(self.config_dir, ExternalDiskManagerDefaults.MAIN_CONF)
            self.hook_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.HOOK_DIR)
            self.additional_config_dir = os.path.join(self.config_dir, ExternalDiskManagerDefaults.ADDITIONAL_CONFIG_DIR)

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

        # load the addition config files
        try:
            self._items = []
            ret = True
            files = os.listdir(self.additional_config_dir)
            for f in files:
                (basename, ext) = os.path.splitext(f)
                if ext == '.conf':
                    fullpath = os.path.join(self.additional_config_dir, f)
                    item = ExternalDiskManagerConfigItem(fullpath)
                    if item.is_valid:
                        self._items.append(item)
                    else:
                        print('config item %s is invalid' % (fullpath))
        except (IOError, OSError) as e:
            self._last_error = str(e)
            ret = False

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

        for item in self._items:
            if not item.save():
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
        ret = True
        for item in iter(self._items):
            if not item.remove():
                ret = False
            del item
        return ret

    def register_disk(self, name, pattern, external=True, tags=[]):
        found = False
        for item in self._items:
            if item.pattern == pattern:
                item.external = external
                item.tags = tags
                found = True
                break
        if not found:
            # create new config item
            newitem = ExternalDiskManagerConfigItem()
            newitem.external = external
            newitem.pattern = pattern
            newitem.tags = tags

            filename = re.sub(r'[\s]', '_', name)
            fullpath = os.path.join(self.additional_config_dir, filename + '.conf')
            newitem.filename = fullpath
            self._items.append(newitem)
            #newitem.save(fullpath)
        return True

    def unregister_disk(self, name, pattern, external=True):
        ret = True
        found = False
        for item in iter(self._items):
            if item.pattern == pattern and item.external == external:
                found = True
                if not item.remove():
                    ret = False
                del item
                break
        return ret

    def get_disks_by_tag(self, tag):
        ret = []
        for item in iter(self._items):
            if tag in item.tags:
                ret.append(item.pattern)
        return ret
    
    def get_tags_for_disk(self, pattern):
        ret = None
        for item in iter(self._items):
            if item.pattern == pattern:
                ret = item.tags
        return ret

    def __str__(self):
        ret = ''
        ret = ret + 'config_dir: ' + str(self.config_dir) + '\n'
        ret = ret + 'hook directory: ' + str(self.hook_dir) + '\n'
        ret = ret + 'add. config directory: ' + str(self.additional_config_dir) + '\n'
        return ret
 
