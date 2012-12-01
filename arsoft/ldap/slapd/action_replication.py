#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import string
import ldap
import ldap.modlist as modlist
from action_base import *

class action_replication(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure the replication')
        parser.add_argument('-a', '--add', dest='add', type=str, nargs='+', help='adds the specified server.')
        parser.add_argument('-r', '--remove', dest='remove', type=str, nargs='+', help='removes the specified server.')
        parser.add_argument('-d', '--database', dest='database', type=str, nargs='+', help='enable replication on the specified database.')
        
        pargs = parser.parse_args(args)

        self._add = pargs.add
        self._remove = pargs.remove
        self._database = pargs.database
        self._server_list = {}

    @staticmethod
    def _parse_serverid(val):
        if val is None:
            return (None, None)
        else:
            endidx = val.find(' ', 0)
            if endidx < 0:
                return (None, val)
            else:
                num = val[0:endidx]
                if num[0] == '0' and num[1] == 'x':
                    serverid = int(num[2:], 16)
                else:
                    serverid = int(num, 10)
                serveruri = val[endidx+1:]
                return (serverid, serveruri)
            
    @staticmethod
    def _format_serverid(val):
        return '0x%x %s' % val

    def _get_server_list(self):
        searchBase = 'cn=config'
        searchFilter = '(objectClass=olcGlobal)'
        attrsFilter = ['olcServerID']
        
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_BASE)
        
        self._server_list = {}
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]

                if 'olcServerID' in values:
                    for val in values['olcServerID']:
                        (serverid, serveruri) = action_replication._parse_serverid(val)
                        if serverid is not None:
                            self._server_list[serverid] = serveruri

            ret = True
        else:
            ret = False
        return ret
    
    def _get_next_serverid(self):
        ret = 1
        used_serverids = self._server_list.keys()
        while ret < 4096:
            if ret in used_serverids:
                ret = ret + 1
            else:
                break
        return ret
    
    def _find_server_by_uri(self, uri):
        ret = None
        for (serverid, serveruri) in self._server_list.items():
            if serveruri == uri:
                ret = serverid
                break
        return ret
    
    def _ensure_syncprov_module(self):
        self._select_modulelist(add_modulelist_if_not_available=True)
        
        if 'syncprov' not in self._modules.values():
            mod_attrs = []
            mod_attrs.append( (ldap.MOD_ADD, 'olcModuleLoad', 'syncprov') )
            ret = self._modify_direct(self._selected_modulelist_dn, mod_attrs)
        else:
            ret = True
        return ret

    def _add_syncprov_to_database(self, database):
        has_syncprov = False
        for overlay in database['overlay'].values():
            if overlay['type'] == 'syncprov':
                has_syncprov = True
                break
        
        if not has_syncprov:
            database_dn = database['dn']
            syncprov_dn = 'olcOverlay=syncprov,' + database_dn
            values = {'objectClass': ['olcConfig', 'olcOverlayConfig', 'olcSyncProvConfig', 'top'],
                    'olcOverlay': 'syncprov'
                    }
            ret = self._add_entry(syncprov_dn, values)
        else:
            ret = True
        return ret

    def _add_syncrepl_to_database(self, database):

        ret = True
        if ret:
            ret = self._set_database_mirrormode(database_dn, true)
        return ret

    def run(self):
        self._get_server_list()
        
        if self._add is None and self._remove is None and self._database is None:
            ret = self._status()
        else:
            mod_attrs = []
            if self._add is not None:
                self._ensure_syncprov_module()
                for server in self._add:
                    (serverid, serveruri) = action_replication._parse_serverid(server)
                    if serverid is None:
                        serverid = self._find_server_by_uri(serveruri)
                        if serverid is None:
                            serverid = self._get_next_serverid()
                            mod_attrs.append( (ldap.MOD_ADD, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )
                    else:
                        mod_attrs.append( (ldap.MOD_ADD, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )

            if self._remove is not None:
                for server in self._remove:
                    found = False
                    (serverid, serveruri) = action_replication._parse_serverid(server)
                    if serverid is None:
                        serverid = self._find_server_by_uri(serveruri)
                        
                    if serverid in self._server_list.keys():
                        found = True
                    else:
                        found = False
                        
                    if found:
                        mod_attrs.append( (ldap.MOD_DELETE, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )

            if self._modify_direct('cn=config', mod_attrs):
                if self._database is not None:
                    self._get_databases()
                    self._get_database_overlays()
                    for database in self._database:
                        db = self._get_database_by_name(database)
                        if db is not None:
                            self._add_syncprov_to_database(db)
                ret = 0
            else:
                ret = 1
        return ret

    def _status(self):
        if len(self._server_list) > 0:
            print("Servers:")
            for serverid in sorted(self._server_list.keys()):
                serveruri = self._server_list[serverid]
                print('  ' + str(serverid) + ': ' + serveruri)
        else:
            print("Servers: <none>")
        return 0
