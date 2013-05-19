#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class BackendInfo(object):
    def __init__(self, module_name, module_description, module_homepage, module_version):
        self.name = module_name
        self.description = module_description
        self.homepage = module_homepage
        self.version = module_version

    def __str__(self):
        ret = str(self.name) + ': ' + str(self.description) + '\n'
        if self.homepage is not None:
            ret = ret + 'Homepage: ' + str(self.homepage) + '\n'
        ret = ret + 'Version: ' + str(self.version) + '\n'
        return ret

class BackendBot(object):
    def __init__(self):
        pass
