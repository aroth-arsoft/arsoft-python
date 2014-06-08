#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import ldap
import ldap.modlist as modlist
import string
from .action_base import *

class action_database(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure a LDAP database')
        parser.add_argument('--readonly', dest='readonly', type=str, choices=['yes', 'no'], help='marks the database as read-only.')
        parser.add_argument('--mirror', dest='mirror', type=str, choices=['yes', 'no'], help='enables/disables the mirror mode of the database.')
        parser.add_argument('--all', dest='show_all', action='store_true', help='shows all databases (internal as well).')
        parser.add_argument('dbname', type=str, nargs='?', help='selects the database by the suffix or database name.')

        pargs = parser.parse_args(args)

        if pargs.readonly is None:
            self._readonly = None
        else:
            self._readonly = True if pargs.readonly == 'yes' else False
        self._dbname = pargs.dbname
        self._selected_database_dn = None
        self._show_internal = True if pargs.show_all else False
        
    def run(self):
        if not self._get_databases():
            return 4
        
        if not self._select_database():
            return 5

        show_db = True
        if self._readonly is not None:
            show_db = False
            ret = self._set_readonly()
        if self._mirror is not None:
            show_db = False
            ret = self._set_mirror()

        if show_db:
            ret = self._show()
        return ret

    def _select_database(self):
        self._selected_database_dn = None
        if self._dbname is not None:
            db = self._get_database_by_name(self._dbname)
            if db is not None:
                self._selected_database_dn = db['dn']
                ret = True
            else:
                self._selected_database_dn = None
                ret = False
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

    def _set_mirror(self):
        if self._mirror == True:
            target_value = {'olcMirrorMode':'TRUE'}
        else:
            target_value = {'olcMirrorMode':'FALSE'}
        if self._update(self._selected_database_dn, target_value):
            ret = 0
        else:
            ret = 1
        return ret

    def _show(self):
        if len(self._databases) > 0:
            self._get_database_overlays()
            for db in self._databases:
                if self._selected_database_dn is not None:
                    show_db = True if self._selected_database_dn == db['dn'] else False
                elif db['internal']:
                    show_db = True if self._show_internal else False
                else:
                    show_db = True
                if show_db:
                    print(('Database: ' + str(db['suffix']) + ' (' + db['type'] + ')'))
                    print(('  dn:        ' + str(db['dn'])))
                    print(('  root dn:   ' + str(db['rootdn'])))
                    if db['readonly'] is not None:
                        print(('  read-only: ' + ('yes' if db['readonly'] == True else 'no')))
                    if db['mirrormode'] is not None:
                        print(('  mirror mode: ' + ('yes' if db['mirrormode'] == True else 'no')))

                    if len(db['index']) != 0:
                        print('  index:')
                        for idx in list(db['index'].values()):
                            print(('    ' + str(idx)))
                    if len(db['access']) != 0:
                        print('  access:')
                        for idx in list(db['access'].values()):
                            print(('    ' + str(idx)))
                    if len(db['config']) != 0:
                        print('  config:')
                        for idx in list(db['config'].values()):
                            print(('    ' + str(idx)))
                    if len(db['overlay']) != 0:
                        print('  overlay:')
                        for overlay in list(db['overlay'].values()):
                            print(('    ' + overlay['name'] + '(' + str(overlay['type']) + ')'))
                    if len(db['replication']) != 0:
                        print('  replication:')
                        for repl in db['replication']:
                            print(('    ' + str(repl)))
        else:
            print("Databases: <none>")
        return 0 
