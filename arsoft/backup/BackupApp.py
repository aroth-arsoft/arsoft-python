#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .FileList import *
from .BackupConfig import *

class BackupApp(object):
    def __init__(self, name=None):
        self.name = name
        self.intermediate_filelist = FileList()
        self.config = BackupConfig()

    def load_config(self, configdir=None):
        self.config.open(configdir)
        return True