#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import string
import ldap
import ldap.modlist as modlist
from action_base import *

class action_status(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

    def run(self):
        searchBase = ''
        searchFilter = '(objectclass=*)'
        attrsFilter = ROOTDSE_ATTRS

        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_BASE)
        rootDSE = None
        namingContexts = []
        saslMechs = []
        configContext = ''
        ldapversion = None
        if result_set is not None:
            (dn, rootDSE) = result_set[0][0]
            if 'namingContexts' in rootDSE:
                namingContexts = rootDSE['namingContexts']
            configContext = rootDSE['configContext'][0]
            ldapversion = rootDSE['supportedLDAPVersion'][0]
            if 'supportedSASLMechanisms' in rootDSE:
                saslMechs = rootDSE['supportedSASLMechanisms']

        print("LDAP uri:        " + str(self._app._uri))
        print("LDAP version:    " + str(ldapversion))
        if len(namingContexts) > 0:
            print("namingContexts:  " + str(string.join(namingContexts, ', ')))
        else:
            print("namingContexts:  <none>")
        print("configContext:   " + str(configContext))
        print("SASL mechanisms: " + str(string.join(saslMechs, ', ')))
        
        if self._local_defaults is not None:
            if self._local_defaults.has_ldapi_service():
                print("LDAPI socket:    enabled")
            else:
                print("LDAPI socket:    disabled")
            print("Public services: " + str(string.join(self._local_defaults.public_services, ', ')))

        return 0
