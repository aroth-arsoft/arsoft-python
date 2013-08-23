#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.filelist import *
from .BackupConfig import *
from .plugin import *
import sys

class BackupApp(object):
    
    class LoadedPlugin(object):
        def __init__(self, plugin_name, plugin_module, plugin_impl):
            self.name = plugin_name
            self.module = plugin_module
            self.impl = plugin_impl
    
    def __init__(self, name=None):
        self.name = name
        self.intermediate_filelist = FileList()
        self.config = BackupConfig()
        self.plugins = []

    def load_config(self, configdir=None):
        self.config.open(configdir)
        
        plugins_to_load = self.config.active_plugins
        for plugin in plugins_to_load:
            if not self._load_plugin(plugin):
                sys.stderr.write('Failed to log plugin %s\n' % plugin)
        return True

    def _load_plugin(self, plugin_name):
        plugin_module_name = "arsoft.backup.plugins." + plugin_name
        try:
            mod = __import__(plugin_module_name)
        except Exception as e:
            print(e)
            mod = None

        subclasses=[]
        if mod:
            #walk the dictionaries to get to the last one
            d=mod.__dict__
            for m in plugin_module_name.split('.')[1:]:
                d=d[m].__dict__
            for (key, entry) in d.iteritems():
                if key.startswith('_') or key == BackupPlugin.__name__:
                    continue

                try:
                    if issubclass(entry, BackupPlugin):
                        subclasses.append(entry)
                except TypeError:
                    #this happens when a non-type is passed in to issubclass. We
                    #don't care as it can't be a subclass of Job if it isn't a
                    #type
                    continue
        
        ret = False
        for subclass in subclasses:
            inst = subclass(self)
            plugin = BackupApp.LoadedPlugin(plugin_name, mod, inst)
            self.plugins.append(plugin)
            ret = True
        return ret

    def _call_plugins(self, cmd, **kwargs):
        for plugin in self.plugins:
            if hasattr(plugin.impl, cmd):
                func = getattr(plugin.impl, cmd)
                if func:
                    func(**kwargs)

    def append_intermediate_filelist(self, filelist_item):
        self.intermediate_filelist.append(filelist_item)

    def plugin_notify_disk_ready(self):
        self._call_plugins('disk_ready')

    def plugin_notify_disk_eject(self):
        self._call_plugins('disk_eject')

    def plugin_notify_start_rsync(self):
        self._call_plugins('start_rsync')

    def plugin_notify_rsync_complete(self):
        self._call_plugins('rsync_complete')

    def plugin_notify_start_backup(self):
        self._call_plugins('start_backup')
    def plugin_notify_perform_backup(self):
        self._call_plugins('perform_backup')
    def plugin_notify_backup_complete(self):
        self._call_plugins('backup_complete')
