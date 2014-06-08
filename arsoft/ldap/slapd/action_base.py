#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import string
import ldap
import ldap.modlist as modlist
import ldif
import socket
from urllib.parse import urlparse
from .syncrepl import *
from .slapd_defaults import *
import arsoft.utils
from arsoft.ldap.cxn import LdapConnection

# Used attributes from RootDSE
ROOTDSE_ATTRS = (
'objectClass',
'altServer',
'namingContexts',
'ogSupportedProfile',
'subschemaSubentry',
'supportedControl',
'supportedExtension',
'supportedFeatures',
'supportedLDAPVersion',
'supportedSASLMechanisms',
'supportedAuthPasswordSchemes', # RFC 3112
'vendorName',
'vendorVersion',
# 'informational' attributes of OpenLDAP
'auditContext',
'configContext',
'monitorContext',
# 'informational' attributes of Active Directory
'configurationNamingContext',
'defaultNamingContext',
'defaultRnrDN',
'dnsHostName',
'schemaNamingContext',
'supportedCapabilities',
'supportedLDAPPolicies',
# 'informational' attributes of IBM Directory Server
'ibm-configurationnamingcontext',
)

class database_list(list):
    def get_config(self):
        for db in self:
            if db['type'] == 'config':
                return db
        return None
        
    def exclude_internal(self):
        ret = []
        for db in self:
            if db['internal'] == True:
                continue
            ret.append(db)
        return ret

class action_base(object):

    def __init__(self, app, args):
        self._app = app
        self._cxn = app._cxn
        self._second_cxn = None
        self._uri = app._uri
        self._args = args
        self._local_defaults = None
        self._ldap_hostname = None
        self._ldap_hostaddr = None

        o = urlparse(self._uri)
        if o.scheme == 'ldap' or o.scheme == 'ldaps':
            self._ldap_hostname = o.hostname
        elif o.scheme == 'ldapi':
            self._ldap_hostname = 'localhost'
        else:
            self._error('Invalid or unsupported URI scheme ' + o.scheme)
            
        if arsoft.utils.is_localhost(self._ldap_hostname):
            self._ldap_hostname = socket.getfqdn()
            self._ldap_hostaddr = socket.gethostbyname(self._ldap_hostname)
            self._local_defaults = slapd_defaults()
        else:
            # keep the value in self._ldap_hostname
            self._ldap_hostaddr = socket.gethostbyname(self._ldap_hostname)
            self._local_defaults = None

    def _verbose(self, msg):
        self._app.verbose(msg)

    def _error(self, msg):
        self._app.error(msg)

    def _warn(self, msg):
        self._app.warn(msg)
        
    def connect(self, uri, username, password, saslmech):
        self._cxn = LdapConnection(uri, username, password, saslmech)
        return self._cxn.connect()

    def close(self):
        self._cxn.close()
        
    @staticmethod
    def _indexvalue(val):
        if val is None:
            return (None, None)
        else:
            if val[0] == '{':
                endidx = val.find('}', 1)
                if endidx < 0:
                    return (None, val)
                else:
                    return (int(val[1:endidx]), val[(endidx+1):])
            else:
                return (None, val)

    @staticmethod
    def _read_ldif_file(filename):
        ret = None
        try:
            f = open(filename, 'rb')
            recordlist = ldif.LDIFRecordList(f)
            recordlist.parse()
            f.close()
            ret = recordlist.all_records
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            ret = None
        return ret
    
    @staticmethod
    def _ldap_error_message(e):
        if type(e.message) == dict:
            msg = ''
            for (k, v) in e.message.items():
                msg = msg + "%s: %s" % (k, v)
        else:
            msg = str(e)
        return msg

    def _connect_second(self, uri):

        uri = action_base.get_full_ldap_uri(uri)

        try:
            self._verbose("Connecting to " + uri + "...")
            self._second_cxn = ldap.initialize(uri)
        except ldap.LDAPError as e:
            msg = action_base._ldap_error_message(e)
            self._error("Failed to connect to ldap server " + uri + ". " + msg)
            self._second_cxn = None

        if self._second_cxn is not None:
            # you should  set this to ldap.VERSION2 if you're using a v2 directory
            self._second_cxn.protocol_version = ldap.VERSION3
            ret = True
        else:
            ret = False
        return ret

    def _bind_second(self, username=None, password=None, saslmech=None):
        # Pass in a valid username and password to get 
        # privileged directory access.
        # If you leave them as empty strings or pass an invalid value
        # you will still bind to the server but with limited privileges.
        
        if username is None:
            username = self._app._username
        if password is None:
            password = self._app._password
        if saslmech is None:
            saslmech = self._app._saslmech

        ldapusername = '' if username is None else username
        ldappassword = '' if password is None else password
        
        try:
            # Any errors will throw an ldap.LDAPError exception 
            # or related exception so you can ignore the result
            if saslmech == 'simple':
                if ldapusername != '':
                    self._verbose("simple_bind user:" + ldapusername + " pwd:" + ldappassword)
                else:
                    self.verbose("simple_bind anonymous")
                self._second_cxn.simple_bind_s(ldapusername, ldappassword)
                ret = True
            else:
                self._verbose('bind ' + saslmech + " user:" + ldapusername + " pwd:" + ldappassword)
                self._second_cxn.bind_s(ldapusername, ldappassword, saslmech)
                ret = True
        except ldap.LDAPError as e:
            msg = action_base._ldap_error_message(e)
            self._error("Failed to bind to ldap server as " + ldapusername + ". " + msg)
            ret = False
        return ret
        
    def _unbind_second(self):
        self._second_cxn.unbind_s()
        self._second_cxn = None

    def _search( self, searchBase, searchFilter, attrsFilter, scope=ldap.SCOPE_ONELEVEL):
        return self._cxn.search(searchBase, searchFilter, attrsFilter, scope)

    def _modify(self, dn, old_values, new_values):
        return self._cxn.modify(dn, old_values, new_values)

    def _modify_direct(self, dn, mod_attrs):
        return self._cxn.modify_direct(dn, mod_attrs)

    def _add_entry(self, dn, values):
        return self._cxn.add_entry(dn, values)

    def _delete_entry(self, dn):
        return self._cxn.delete_entry(dn)
    
    def _update(self, dn, values):
        return self._cxn.update(dn, values)

    def _select_modulelist(self, add_modulelist_if_not_available=False):
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
        else:
            if add_modulelist_if_not_available:
                ret = self._add_modulelist()
            else:
                ret = False

        return ret
    
    def _has_config_access(self):
        searchBase = 'cn=config'
        searchFilter = '(objectClass=olcGlobal)'
        attrsFilter = ['cn']
        
        results = self._cxn.search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_BASE)
        if results is None:
            ret = False
        else:
            ret = True
        return ret

    def _add_modulelist(self):
        dn = 'cn=module, cn=config'
        values = { 'objectClass': 'olcModuleList', 'cn':'module'}

        if self._add_entry(dn, values):
            ret = self._select_modulelist()
        else:
            ret = False
        return ret

    def _get_databases(self):
        searchBase = 'cn=config'
        searchFilter = '(&(objectClass=olcDatabaseConfig)(olcDatabase=*))'
        attrsFilter = ['objectClass', 'olcDatabase', 'olcDbDirectory', 'olcSuffix', 'olcReadOnly', 'olcRootDN', 'olcRootPW', 'olcAccess', 'olcDbConfig', 'olcDbIndex', 'olcSyncrepl', 'olcMirrorMode']

        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        self._databases = database_list()
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                cn_elems = string.split(values['olcDatabase'][0], ',')
                (dbno, dbtype) = action_base._indexvalue(cn_elems[0])
                dbtype = dbtype.lower()

                index = {}
                access = {}
                config = {}
                repl = {}
                if 'olcDbIndex' in values:
                    for v in values['olcDbIndex']:
                        (indexno, indexline) = action_base._indexvalue(v)
                        index[indexno] = indexline
                if 'olcAccess' in values:
                    for v in values['olcAccess']:
                        (accessno, accessline) = action_base._indexvalue(v)
                        access[accessno] = accessline
                if 'olcDbConfig' in values:
                    for v in values['olcDbConfig']:
                        (configno, configline) = action_base._indexvalue(v)
                        config[configno] = configline
                if 'olcSyncrepl' in values:
                    for v in values['olcSyncrepl']:
                        (replno, replline) = action_base._indexvalue(v)
                        repl[replno] = syncrepl(replline)
                if dbtype == 'frontend':
                    searchbase = None
                    name = 'frontend'
                elif dbtype == 'config':
                    searchbase = 'cn=config'
                    name = 'cn=config'
                else:
                    searchbase = values['olcSuffix'][0] if 'olcSuffix' in values else None
                    name = searchbase
                database = {'dn': dn,
                            'name': name,
                            'objectclass': values['objectClass'],
                            'type': dbtype, 
                            'suffix': values['olcSuffix'][0] if 'olcSuffix' in values else None,
                            'defaultsearchbase': searchbase,
                            'internal': True if dbtype == 'frontend' or dbtype == 'config' else False,
                            'rootdn': values['olcRootDN'][0] if 'olcRootDN' in values else None,
                            'rootpw': values['olcRootPW'][0] if 'olcRootPW' in values else None,
                            'readonly': (True if values['olcReadOnly'][0].lower() == 'true' else False ) if 'olcReadOnly' in values else None,
                            'mirrormode': (True if values['olcMirrorMode'][0].lower() == 'true' else False ) if 'olcMirrorMode' in values else None,
                            'dbdir': values['olcDbDirectory'][0] if 'olcDbDirectory' in values else None,
                            'index': index,
                            'access': access,
                            'config': config,
                            'replication': repl,
                            'overlay': {}
                            }
                self._databases.append(database)
            ret = True
        else:
            ret = False
        return ret

    def _get_database_by_name(self, dbname):
        for db in self._databases:
            if db['suffix'] == dbname:
                return db
            elif db['internal'] == True and db['type'] == dbname:
                return db
        return None
        
    def _get_database_overlays(self):
        i = 0
        while i < len(self._databases):
            db_overlays = self._get_overlays_for_database(self._databases[i]['dn'])
            if db_overlays is not None:
                self._databases[i]['overlay'] = db_overlays
            i = i + 1
        return True

    def _get_overlays_for_database(self, database_dn):
        searchBase = database_dn
        searchFilter = '(objectClass=olcOverlayConfig)'
        attrsFilter = ['objectClass', 'olcOverlay']
        
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        overlays = {}
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]

                (overlayno, overlayname) = action_base._indexvalue(values['olcOverlay'][0])
                if 'olcSyncProvConfig' in values['objectClass']:
                    overlaytype = 'syncprov'
                else:
                    overlaytype = None
                overlay = { 'name': overlayname,
                            'type': overlaytype 
                            }
                overlays[overlayno] = overlay
            ret = True
        else:
            ret = False

        return overlays if ret else None

    def _set_database_mirrormode(self, database_dn, enable):
        if enable == True:
            target_value = {'olcMirrorMode':'TRUE'}
        else:
            target_value = {'olcMirrorMode':'FALSE'}
        return self._update(self._selected_database_dn, target_value)
