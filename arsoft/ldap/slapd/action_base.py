#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import string
import ldap
import ldap.modlist as modlist
import ldif
from syncrepl import *

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

class action_base(object):

    def __init__(self, app, args):
        self._app = app
        self._cxn = app._cxn
        self._args = args

    def _verbose(self, msg):
        self._app.verbose(msg)

    def _error(self, msg):
        self._app.error(msg)
        
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

    def _search( self, searchBase, searchFilter, attrsFilter, scope=ldap.SCOPE_ONELEVEL):
        
        self._verbose('searchBase ' + searchBase)
        self._verbose('searchFilter ' + searchFilter)
        self._verbose('attrsFilter ' + str(attrsFilter))
        result_set = []
        try:
            ldap_result_id = self._cxn.search(searchBase, scope, searchFilter, attrsFilter)
            while 1:
                result_type, result_data = self._cxn.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    ## here you don't have to append to a list
                    ## you could do whatever you want with the individual entry
                    ## The appending to list is just for illustration. 
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            result_set = None
            pass
        return result_set

    def _modify(self, dn, old_values, new_values):
        self._verbose('dn ' + dn)
        self._verbose('old_values ' + str(old_values))
        self._verbose('new_values ' + str(new_values))
        mod_attrs = ldap.modlist.modifyModlist(old_values, new_values)
        self._verbose('mod_attrs ' + str(mod_attrs))
        try:
            self._cxn.modify_s(dn, mod_attrs)
            ret = True
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            ret = False
        return ret

    def _modify_direct(self, dn, mod_attrs):
        self._verbose('dn ' + dn)
        self._verbose('mod_attrs ' + str(mod_attrs))
        if len(mod_attrs) == 0:
            ret = True
        else:
            try:
                self._cxn.modify_s(dn, mod_attrs)
                ret = True
            except ldap.LDAPError as e:
                self._error('ldaperror: ' + str(e))
                ret = False
        return ret

    def _add_entry(self, dn, values):
        add_attrs = ldap.modlist.addModlist(values)
        try:
            self._cxn.add_s(dn, add_attrs)
            ret = True
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            ret = False
        return ret

    def _delete_entry(self, dn):
        try:
            self._cxn.delete_s(dn)
            ret = True
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            ret = False
        return ret
    
    def _update(self, dn, values):
        searchBase = dn
        searchFilter = '(objectClass=*)'
        attrsFilter = values.keys()
        
        mod_old_values = {}
        mod_new_values = {}
        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_BASE)
        if result_set is not None:
            for rec in result_set:
                (dn, current_values) = rec[0]
                
                for (key, current_value) in current_values.items():
                    if values[key] == current_value:
                        # value already up-to-date
                        continue
                    else:
                        # add the old and new value to the dict for
                        # the modify op
                        mod_old_values[key] = current_value
                        mod_new_values[key] = values[key]
        for (key, new_value) in values.items():
            if key not in mod_new_values:
                mod_new_values[key] = new_value
        self._modify(dn, mod_old_values, mod_new_values)

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
        self._databases = []
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
                elif dbtype == 'config':
                    searchbase = 'cn=config'
                else:
                    searchbase = values['olcSuffix'][0] if 'olcSuffix' in values else None
                database = {'dn': dn,
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
