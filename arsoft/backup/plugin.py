#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .BackupConfig import BackupPluginConfig

class BackupPlugin(object):
    def __init__(self, backup_app, name):
        self.name = name
        self.backup_app = backup_app
        self.config = BackupPluginConfig(parent=backup_app.config, plugin_name=self.name)

