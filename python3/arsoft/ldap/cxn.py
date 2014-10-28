#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import ldap
import ldap.modlist as modlist

from utils import *

class LdapConnection(object):
    def __init__(self, uri=None, username=None, password=None, saslmech='simple', logger=None):
        self._cxn = None
        self._uri = uri
        self._username = username
        self._password = password
        self._saslmech = saslmech
        self._logger = logger

    def _verbose(self, msg):
        if self._logger is not None:
            self._logger.verbose(msg)
            
    def _error(self, msg):
        if self._logger is not None:
            self._logger.error(msg)

    @staticmethod
    def _ldap_error_message(e):
        if type(e.message) == dict:
            msg = ''
            for (k, v) in e.message.iteritems():
                msg = msg + "%s: %s" % (k, v)
        else:
            msg = str(e)
        return msg

    def connect(self, uri=None, username=None, password=None, saslmech=None):
        if uri is None:
            uri = self._uri
        if username is None:
            username = self._username
        if password is None:
            password = self._password
        if saslmech is None:
            saslmech = self._saslmech
        uri = get_full_ldap_uri(uri)

        try:
            self._cxn = ldap.initialize(uri)
        except ldap.LDAPError as e:
            msg = LdapConnection._ldap_error_message(e)
            self._cxn = None

        if self._cxn is not None:
            # you should  set this to ldap.VERSION2 if you're using a v2 directory
            self._cxn.protocol_version = ldap.VERSION3
            ret = True
        else:
            ret = False
            
        if ret:
            ldapusername = '' if username is None else username
            ldappassword = '' if password is None else password
            
            try:
                # Any errors will throw an ldap.LDAPError exception 
                # or related exception so you can ignore the result
                if saslmech == 'simple':
                    if ldapusername != '':
                        self._verbose("simple_bind user:%s pwd:%s" % (ldapusername,ldappassword))
                    else:
                        self._verbose("simple_bind anonymous")
                    self._cxn.simple_bind_s(ldapusername, ldappassword)
                    ret = True
                else:
                    self._verbose('bind mech:%s user:%s pwd:%s' % (saslmech, ldapusername,ldappassword))
                    self._cxn.bind_s(ldapusername, ldappassword, saslmech)
                    ret = True
            except ldap.LDAPError as e:
                msg = LdapConnection._ldap_error_message(e)
                self._error("Failed to bind to ldap server as %s: %s" % (ldapusername, msg))
                ret = False
        return ret
        
    def close(self):
        self._cxn.unbind_s()
        self._cxn = None

    def search( self, searchBase, searchFilter, attrsFilter, scope=ldap.SCOPE_ONELEVEL):
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
            msg = LdapConnection._ldap_error_message(e)
            self._error('ldap search on %s for %s failed: %s' (searchBase, searchFilter, msg))
            result_set = None
            pass
        return result_set

    def modify(self, dn, old_values, new_values):
        self._verbose('dn ' + dn)
        self._verbose('old_values ' + str(old_values))
        self._verbose('new_values ' + str(new_values))
        mod_attrs = ldap.modlist.modifyModlist(old_values, new_values)
        self._verbose('mod_attrs ' + str(mod_attrs))
        try:
            self._cxn.modify_s(dn, mod_attrs)
            ret = True
        except ldap.LDAPError as e:
            msg = LdapConnection._ldap_error_message(e)
            self._error('ldap modify ' + str(dn) + ' failed: ' + msg)
            ret = False
        return ret

    def modify_direct(self, dn, mod_attrs):
        self._verbose('dn ' + dn)
        self._verbose('mod_attrs ' + str(mod_attrs))
        if len(mod_attrs) == 0:
            ret = True
        else:
            try:
                self._cxn.modify_s(dn, mod_attrs)
                ret = True
            except ldap.LDAPError as e:
                msg = LdapConnection._ldap_error_message(e)
                self._error('ldap modify ' + str(dn) + ' failed: ' + msg)
                ret = False
        return ret

    def add_entry(self, dn, values):
        add_attrs = ldap.modlist.addModlist(values)
        try:
            self._cxn.add_s(dn, add_attrs)
            ret = True
        except ldap.LDAPError as e:
            msg = LdapConnection._ldap_error_message(e)
            self._error('ldap add ' + str(dn) + ' failed: ' + msg)
            ret = False
        return ret

    def delete_entry(self, dn):
        try:
            self._cxn.delete_s(dn)
            ret = True
        except ldap.LDAPError as e:
            msg = LdapConnection._ldap_error_message(e)
            self._error('ldap delete ' + str(dn) + ' failed: ' + msg)
            ret = False
        return ret
    
    def update(self, dn, values):
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
        return self._modify(dn, mod_old_values, mod_new_values)
