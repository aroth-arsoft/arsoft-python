#!/usr/bin/python

import argparse
import string
import ldap
import ldap.modlist as modlist
from .action_base import *

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
        
    def _add_ldif_schema(self, filename):
        recordlist = action_base._read_ldif_file(filename)
        if recordlist is not None:
            ret = True
            for (dn, record) in recordlist:
                if not self._add_entry(dn, record):
                    ret = False
                    break;
        else:
            ret = False
        return ret
        
    def _find_schema_dn(self, schemaname):
        searchBase = self._selected_schemaconfig_dn
        searchFilter = '(&(objectClass=olcSchemaConfig)(cn=*' + schemaname + '))'
        attrsFilter = ['cn']
        
        ret = None
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                ret = dn
                break
        return ret

    def _remove_schema(self, schemaname):
        schema_dn = self._find_schema_dn(schemaname)
        if schema_dn is not None:
            ret = self._delete_entry(schema_dn)
            if not ret:
                self._error('Failed to delete schema ' + schema_dn)
        else:
            self._error('Cannot find schema ' + schemaname)
            ret = False
        return ret

    def run(self):
        self._select_schemaconfig()
        
        if self._add is None and self._remove is None:
            ret = self._list()
        else:
            if self._add is not None:
                ret = 0
                for schemafile in self._add:
                    if not self._add_ldif_schema(schemafile):
                        self._error('Failed to add schema from file ' + schemafile)
                        ret = 1
            if self._remove is not None:
                ret = 0
                for schemaname in self._remove:
                    if not self._remove_schema(schemaname):
                        ret = 1

        return ret

    def _list(self):
        if len(self._schemas) > 0:
            print("Schemas:")
            for schemaidx in sorted(self._schemas.keys()):
                schemaname = self._schemas[schemaidx]
                print(('  ' + schemaname))
        else:
            print("Schemas: <none>")
        return 0 
