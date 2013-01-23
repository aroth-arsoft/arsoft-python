#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class kernel_module(object):
    _instance = None

    def __init__(self):
        self._list = None
        
    @staticmethod
    def instance():
        if kernel_module._instance is None:
            kernel_module._instance = kernel_module()
        return kernel_module._instance

    @staticmethod
    def get_module_list():
        obj = kernel_module.instance()
        return obj._get_list()

    @staticmethod
    def is_module_loaded(modname):
        obj = kernel_module.instance()
        modlist = obj._get_list()
        ret = True if modname in modlist.keys() else False
        return ret

    def _update_list(self):
        self._list = {}
        try:
            f = open('/proc/modules', 'r')
            for line in f:
                elems = line.split(' ')
                (modname, modsize, usecount, users, status, address) = elems[0:6]
                modusers = []
                if users != '-':
                    for u in users.split(','):
                        if len(u) > 0:
                            modusers.append(u)
                self._list[modname] = (int(modsize), int(usecount), users, address) 
        except IOError:
            pass

    def _get_list(self):
        if self._list is None:
            self._update_list()
        return self._list
