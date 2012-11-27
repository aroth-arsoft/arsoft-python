#!/usr/bin/python

import argparse
import string
import ldap
import ldap.modlist as modlist
from action_base import *

class action_schema(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure the loaded schemas')
        parser.add_argument('-a', '--add', dest='add', type=str, nargs='+', help='adds the specified schema.')
        parser.add_argument('-r', '--remove', dest='remove', type=str, nargs='+', help='removes the specified schema.')

        pargs = parser.parse_args(args)
        self._add = pargs.add
        self._remove = pargs.remove
        self._selected_schemaconfig_dn = None

    def _select_schemaconfig(self):
        self._selected_schemaconfig_dn = None
        self._schemas = {}

        searchBase = 'cn=config'
        searchFilter = '(&(objectClass=olcSchemaConfig)(cn=*))'
        attrsFilter = ['cn']
        
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                self._selected_schemaconfig_dn = dn

        ret = True if self._selected_schemaconfig_dn is not None else False
        
        if ret:
            searchBase = self._selected_schemaconfig_dn
            searchFilter = '(&(objectClass=olcSchemaConfig)(cn=*))'
            attrsFilter = ['cn']
            
            result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
            
            if result_set is not None:
                for rec in result_set:
                    (dn, values) = rec[0]
                    (schemaidx, schemaname) = action_base._indexvalue(values['cn'][0])
                    self._schemas[schemaidx] = schemaname
        return ret

    def run(self):
        self._select_schemaconfig()
        
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
        if len(self._schemas) > 0:
            print("Schemas:")
            for schemaidx in sorted(self._schemas.keys()):
                schemaname = self._schemas[schemaidx]
                print('  ' + schemaname)
        else:
            print("Schemas: <none>")
        return 0 
