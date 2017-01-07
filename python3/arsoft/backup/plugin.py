#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .BackupConfig import BackupPluginConfig

class BackupPlugin(object):
    def __init__(self, backup_app, name):
        self.name = name
        self.backup_app = backup_app
        if not hasattr(self, 'config'):
            self.config = BackupPluginConfig(backup_app=backup_app.config, plugin_name=self.name)
        # load the configuration of this plugin on start
        self.config.load()

    def _mkdir(self, dirname):
        # forward request to app
        return self.backup_app._mkdir(dirname)

    @property
    def logfile_proxy(self):
        return self.backup_app.session.logfile_proxy

    def writelog(self, msg):
        return self.backup_app.session.writelog(msg, plugin=self.name)
