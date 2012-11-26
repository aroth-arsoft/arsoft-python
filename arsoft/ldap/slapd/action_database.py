#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import ldap
import ldap.modlist as modlist
import string
from action_base import *

class action_database(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure a LDAP database')
        parser.add_argument('-r', '--readonly', dest='readonly', type=str, choices=['yes', 'no'], help='marks the database as read-only.')
        parser.add_argument('--all', dest='show_all', action='store_true', help='shows all databases (internal as well).')
        parser.add_argument('suffix', type=str, nargs='?', help='selects the database by the suffix.')

        pargs = parser.parse_args(args)

        if pargs.readonly is None:
            self._readonly = None
        else:
            self._readonly = True if pargs.readonly == 'yes' else False
        self._suffix = pargs.suffix
        self._selected_database_dn = None
        self._show_internal = True if pargs.show_all else False
        
    def run(self):
        if not self._select_database():
            return 4
        
        show_db = True
        if self._readonly is not None:
            show_db = False
            ret = self._set_readonly()

        if show_db:
            ret = self._show()
        return ret

    def _select_database(self):
        self._selected_database_dn = None
        if self._suffix is not None:
            searchBase = 'cn=config'
            searchFilter = '(&(objectClass=olcDatabaseConfig)(olcDatabase=*)(olcSuffix=' + self._suffix + '))'
            attrsFilter = []

            result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
            if result_set is not None:
                for rec in result_set:
                    (dn, values) = rec[0]
                    self._selected_database_dn = dn
            ret = True if self._selected_database_dn is not None else False
        else:
            ret = True
        return ret

    def _set_readonly(self):
        if self._readonly == True:
            target_value = {'olcReadOnly':'TRUE'}
        else:
            target_value = {'olcReadOnly':'FALSE'}
        if self._update(self._selected_database_dn, target_value):
            ret = 0
        else:
            ret = 1
        return ret

    def _show(self):
        if self._selected_database_dn is None:
            searchBase = 'cn=config'
        else:
            searchBase = self._selected_database_dn
        searchFilter = '(&(objectClass=olcDatabaseConfig)(olcDatabase=*))'
        attrsFilter = ['olcDatabase', 'olcDbDirectory', 'olcSuffix', 'olcReadOnly', 'olcRootDN', 'olcAccess', 'olcDbConfig', 'olcDbIndex']
        
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        databases = []
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                cn_elems = string.split(values['olcDatabase'][0], ',')
                (dbno, dbtype) = action_base._indexvalue(cn_elems[0])

                index = []
                access = []
                config = []
                if 'olcDbIndex' in values:
                    for v in values['olcDbIndex']:
                        (indexno, indexline) = action_base._indexvalue(v)
                        index.append(indexline)
                if 'olcAccess' in values:
                    for v in values['olcAccess']:
                        (accessno, accessline) = action_base._indexvalue(v)
                        access.append(accessline)
                if 'olcDbConfig' in values:
                    for v in values['olcDbConfig']:
                        (configno, configline) = action_base._indexvalue(v)
                        config.append(configline)
                database = {'type': dbtype, 
                            'suffix': values['olcSuffix'][0] if 'olcSuffix' in values else None,
                            'internal': True if dbtype == 'frontend' or dbtype == 'config' else False,
                            'rootdn': values['olcRootDN'][0] if 'olcRootDN' in values else None,
                            'readonly': (True if values['olcReadOnly'][0] == 'true' else False ) if 'olcReadOnly' in values else None,
                            'dbdir': values['olcDbDirectory'][0] if 'olcDbDirectory' in values else None,
                            'index': index,
                            'access': access,
                            'config': config
                            }
                databases.append(database)

        if len(databases) > 0:
            for db in databases:
                if db['internal']:
                    show_db = True if self._show_internal else False
                else:
                    show_db = True
                if show_db:
                    print('Database: ' + str(db['suffix']) + ' (' + db['type'] + ')')
                    print('  root dn:   ' + str(db['rootdn']))
                    if db['readonly'] is not None:
                        print('  read-only: ' + ('yes' if db['readonly'] == True else 'no'))

                    if len(db['index']) != 0:
                        print('  index:')
                        for idx in db['index']:
                            print('    ' + str(idx))
                    if len(db['access']) != 0:
                        print('  access:')
                        for idx in db['access']:
                            print('    ' + str(idx))
                    if len(db['config']) != 0:
                        print('  config:')
                        for idx in db['config']:
                            print('    ' + str(idx))
        else:
            print("Databases: <none>")
        return 0 
