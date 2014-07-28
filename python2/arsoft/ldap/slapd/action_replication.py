#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import argparse
import string
import ldap
import ldap.modlist as modlist
from urlparse import urlparse
from action_base import *
from syncrepl import *
import arsoft.utils
import arsoft.ldap.utils

class action_replication(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

        parser = argparse.ArgumentParser(description='configure the replication')
        parser.add_argument('-c', '--connect', dest='connect', type=str, nargs='+', help='connects the server to the specified server.')
        parser.add_argument('-a', '--add', dest='add', type=str, nargs='+', help='adds the specified server.')
        parser.add_argument('-r', '--remove', dest='remove', type=str, nargs='+', help='removes the specified server.')
        
        pargs = parser.parse_args(args)

        self._add = pargs.add
        self._remove = pargs.remove
        self._connect = pargs.connect
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
        self._own_serverid = None
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                if 'olcServerID' in values:
                    for val in values['olcServerID']:
                        (serverid, serveruri) = action_replication._parse_serverid(val)
                        if serverid is not None:
                            self._server_list[serverid] = serveruri
                            if self._local_defaults is not None:
                                self._local_defaults.has_service(serveruri)
                                self._own_serverid = serverid
                            else:
                                o = urlparse(serveruri)
                                if o.hostname == self._ldap_hostname or o.hostname == self._ldap_hostaddr:
                                    self._own_serverid = serverid
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

    def _get_next_rid(self):
        ret = 1
        used_rids = []
        for db in self._databases:
            for repl in db['replication'].values():
                used_rids.append(repl.rid)
        while ret < 4096:
            if ret in used_rids:
                ret = ret + 1
            else:
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
        print('_add_syncrepl_to_database ' + str(database))
        print('_add_syncrepl_to_database ' + str(self._server_list))

        mod_attrs = []
        for (serverid, serveruri) in self._server_list.items():
            print('_add_syncrepl_to_database check for server ' + str(serveruri))
            server_has_syncrepl = False
            for repl in database['replication'].values():
                if repl.provider == serveruri:
                    server_has_syncrepl = True
                    break
            if server_has_syncrepl == False:
                db_repl = syncrepl()
                db_repl.rid = self._get_next_rid()
                db_repl.searchbase = database['defaultsearchbase']
                db_repl.provider = serveruri
                db_repl.binddn = database['rootdn']
                db_repl.credentials = database['rootpw']
                db_repl.bindmethod = 'simple'
                
                if db_repl.has_credentials():
                    mod_attrs.append( (ldap.MOD_ADD, 'olcSyncRepl', str(db_repl) ) )
                else:
                    self._warn('Database ' + database['name'] + 'does not have any usable credentials specified.')

        if database['mirrormode'] is None:
            mod_attrs.append( (ldap.MOD_ADD, 'olcMirrorMode', 'TRUE' ) )
        elif database['mirrormode'] == False:
            mod_attrs.append( (ldap.MOD_REPLACE, 'olcMirrorMode', 'TRUE' ) )

        ret = self._modify_direct(database['dn'], mod_attrs)
        return ret
    
    def _set_mirrormode_to_database(self, database):
        print('_set_mirrormode_to_database ' + str(database))
        mod_attrs = []
        if database['mirrormode'] is None:
            mod_attrs.append( (ldap.MOD_ADD, 'olcMirrorMode', 'TRUE' ) )
        elif database['mirrormode'] == False:
            mod_attrs.append( (ldap.MOD_REPLACE, 'olcMirrorMode', 'TRUE' ) )

        ret = self._modify_direct(database['dn'], mod_attrs)
        return ret
    
    def _add_server(self, serverid, serveruri):
        o = urlparse(serveruri)
        if arsoft.utils.is_localhost(o.hostname) or arsoft.utils.is_localhost(serveruri):
            if self._local_defaults is None:
                self._error('Cannot add server with URI to localhost.')
                return False
            else:
                if len(self._local_defaults.public_services) == 1:
                    self._verbose('use server uri ' + self._local_defaults.public_services[0] + ' instead of ' + serveruri)
                    serveruri = self._local_defaults.public_services[0]
                else:
                    self._error('Cannot add server with URI to localhost and cannot determine valid URI from public services.')
                    return False

        self._ensure_syncprov_module()
        
        mod_attrs = []
        server_already_exists = False
        if serverid is None:
            serverid = self._find_server_by_uri(serveruri)
            if serverid is None:
                serverid = self._get_next_serverid()
                # add server
                mod_attrs.append( (ldap.MOD_ADD, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )
            else:
                server_already_exists = True
        else:
            current_serveruri = self._server_list[serverid]
            if current_serveruri == serveruri:
                server_already_exists = True
            else:
                # need to modify a specific server (e.g. server uri has changed)
                # keep serverid, but modify the URI
                mod_attrs.append( (ldap.MOD_REPLACE, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )
        ret = self._modify_direct('cn=config', mod_attrs)
        if ret:
            # refresh the server list and determine again if the connected server
            # has a valid id
            self._get_server_list()
            if self._own_serverid is None or self._own_serverid < 0:
                self._error('Unable to determine the server id for the connected LDAP server. Refuse to add database replication to avoid further trouble.')
            else:
                self._get_databases()
                self._get_database_overlays()
                # now ensure the list of servers is up-to-date in each database
                for db in self._databases.exclude_internal():
                    if not self._add_syncprov_to_database(db):
                        ret = False
                        break
                    elif not self._add_syncrepl_to_database(db):
                        ret = False
                        break
                    elif not self._set_mirrormode_to_database(db):
                        ret = False
                        break

                if ret:
                    # done with all regular databases and now configure
                    # the config database as well
                    db = self._databases.get_config()
                    if db is not None:
                        if not self._add_syncprov_to_database(db):
                            ret = False
                        elif not self._add_syncrepl_to_database(db):
                            ret = False
                        elif not self._set_mirrormode_to_database(db):
                            ret = False
                    else:
                        ret = False

        return ret

    def _remove_syncrepl_from_database(self, database, serveruri):
        print('_remove_syncrepl_from_database ' + str(database))
        print('_remove_syncrepl_from_database ' + str(self._server_list))
        server_has_syncrepl = False
        mod_attrs = []
        for (replno, repl) in database['replication'].items():
            if repl.provider == serveruri:
                server_has_syncrepl = True
                mod_attrs.append( (ldap.MOD_DELETE, 'olcSyncRepl', '{' + str(replno) + '}' + repl.original_string() ) )
                break
        ret = self._modify_direct(database['dn'], mod_attrs)
        return ret

    def _remove_server(self, serverid):
        serveruri = self._server_list[serverid]

        self._get_databases()
        ret = True
        # remove the syncrepl line for this server from all databases
        for db in self._databases:
            if db['type'] == 'frontend':
                continue
            if not self._remove_syncrepl_from_database(db, serveruri):
                ret = False

        if ret:
            # finally remove the server from the global config
            mod_attrs = []
            mod_attrs.append( (ldap.MOD_DELETE, 'olcServerID', action_replication._format_serverid( (serverid, serveruri) ) ) )
            ret = self._modify_direct('cn=config', mod_attrs)
        return ret
    
    def _connect_server(self, remote_server, options):
        # only configure the cn=config database to sync to remote_server
        full_uri = arsoft.ldap.get_full_ldap_uri(remote_server)
        if full_uri == self._uri:
            self._error('Cannot connect this server to itself.')
            ret = False
        else:
            if self._connect_second(remote_server):
                if self._bind_second():
                    self._verbose('Connected to ' + remote_server)
                    ret = True
                    self._unbind_second()
                else:
                    self._error('Unable to bind to remote server ' + remote_server)
                    ret = False
            else:
                self._error('Unable to connect to remote server ' + remote_server)
                ret = False
        return ret

    def _status(self):
        if len(self._server_list) > 0:
            print("Replication servers:")
            for serverid in sorted(self._server_list.keys()):
                serveruri = self._server_list[serverid]
                if self._own_serverid == serverid:
                    print('  ' + str(serverid) + ': ' + serveruri + ' (current server)')
                else:
                    print('  ' + str(serverid) + ': ' + serveruri)
            if self._own_serverid is not None and self._own_serverid < 0:
                print('  No server id for the LDAP server ' + self._ldap_hostname + ' or ' + self._ldap_hostaddr + ' configured.')
        else:
            print("No replication configured.")
        return 0

    def run(self):
        if not self._has_config_access():
            self._error('No access to online configuration of the LDAP server. Please use proper username and password to access the LDAP server.')
            return 1
        self._get_server_list()

        if self._add is None and self._remove is None and self._connect is None:
            ret = self._status()
        elif self._connect is not None:
            remote_server = self._connect[0]
            if len(self._connect) > 1:
                options = self._connect[1:]
            else:
                options = []
            # connect cannot be compined with add and/or remove
            if not self._connect_server(remote_server, options):
                ret = 1
            else:
                ret = 0
        else:
            ret = 0
            if self._add is not None:
                self._ensure_syncprov_module()
                for server in self._add:
                    (serverid, serveruri) = action_replication._parse_serverid(server)
                    if not self._add_server(serverid, serveruri):
                        self._error('Failed to add server with serverid ' + str(serverid) + ' and URI ' + str(serveruri))
                        ret = 1

            if self._remove is not None:
                for server in self._remove:
                    found = False
                    (serverid, serveruri) = action_replication._parse_serverid(server)
                    if serverid is None:
                        serverid = self._find_server_by_uri(serveruri)
                        
                    if serverid not in self._server_list.keys():
                        self._error('Server with serverid ' + str(serverid) + ' and URI ' + str(serveruri) + ' not found.')
                        ret = 1
                        break
                    if not self._remove_server(serverid):
                        self._error('Failed to remove server with serverid ' + str(serverid) + ' and URI ' + str(serveruri))
                        ret = 1

        return ret
