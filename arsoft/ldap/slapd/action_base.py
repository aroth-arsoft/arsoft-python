#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import ldap
import ldap.modlist as modlist

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

    def _add(self, dn, values):
        add_attrs = ldap.modlist.addModlist(values)
        try:
            self._cxn.add_s(dn, add_attrs)
            ret = True
        except ldap.LDAPError as e:
            self._error('ldaperror: ' + str(e))
            ret = False
        return ret

    def _delete(self, dn):
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
