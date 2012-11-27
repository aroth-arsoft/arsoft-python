#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import string
import ldap
import ldap.modlist as modlist
from action_base import *

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

    def _select_modulelist(self):
        self._selected_modulelist_dn = None
        self._modulepath = None
        self._modules = {}

        searchBase = 'cn=config'
        searchFilter = '(&(objectClass=olcModuleList)(cn=*))'
        attrsFilter = ['cn', 'olcModuleLoad', 'olcModulePath']
        
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                self._selected_modulelist_dn = dn
                
                self._modulepath = values['olcModulePath'][0] if 'olcModulePath' in values else None
                if 'olcModuleLoad' in values:
                    for modload in values['olcModuleLoad']:
                        (modidx, modulename) = action_base._indexvalue(modload)
                        self._modules[modidx] = modulename

        ret = True if self._selected_modulelist_dn is not None else False
        return ret

    def run(self):
        self._select_modulelist()
        
        if self._add is None and self._remove is None:
            ret = self._list()
        else:
            mod_attrs = []
            if self._add is not None:
                for mod in self._add:
                    if mod not in self._modules.values():
                        mod_attrs.append( (ldap.MOD_ADD, 'olcModuleLoad', mod) )
            if self._remove is not None:
                for mod in self._remove:
                    found = False
                    for (modidx, modname) in self._modules.items():
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
        print("Modulepath: " + (self._modulepath if self._modulepath is not None else '<default>'))
        if len(self._modules) > 0:
            print("Modules:")
            for modidx in sorted(self._modules.keys()):
                modname = self._modules[modidx]
                print('  ' + modname)
        else:
            print("Modules: <none>")
        return 0
