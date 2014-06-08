#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import string
import ldap
import ldap.modlist as modlist
from .action_base import *

class action_module(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure the loaded modules')
        parser.add_argument('-a', '--add', dest='add', type=str, nargs='+', help='adds the specified module.')
        parser.add_argument('-r', '--remove', dest='remove', type=str, nargs='+', help='removes the specified module.')

        pargs = parser.parse_args(args)
        self._add = pargs.add
        self._remove = pargs.remove
        self._selected_modulelist_dn = None

    def run(self):
        if self._add is None and self._remove is None:
            self._select_modulelist(add_modulelist_if_not_available=False)
            ret = self._list()
        else:
            self._select_modulelist(add_modulelist_if_not_available=True)
            mod_attrs = []
            if self._add is not None:
                for mod in self._add:
                    if mod not in list(self._modules.values()):
                        mod_attrs.append( (ldap.MOD_ADD, 'olcModuleLoad', mod) )
            if self._remove is not None:
                for mod in self._remove:
                    found = False
                    for (modidx, modname) in list(self._modules.items()):
                        if modname == mod:
                            found = True
                            mod_attrs.append( (ldap.MOD_DELETE, 'olcModuleLoad', '{' + str(modidx) + '}' + mod) )
                            break

            if self._modify_direct(self._selected_modulelist_dn, mod_attrs):
                ret = 0
            else:
                ret = 1
        return ret

    def _list(self):
        print(("Modulepath: " + (self._modulepath if self._modulepath is not None else '<default>')))
        if len(self._modules) > 0:
            print("Modules:")
            for modidx in sorted(self._modules.keys()):
                modname = self._modules[modidx]
                print(('  ' + modname))
        else:
            print("Modules: <none>")
        return 0
