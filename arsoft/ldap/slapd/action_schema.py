#!/usr/bin/python

import ldap
import ldap.modlist as modlist
from action_base import *

class action_schema(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

    def run(self):
        searchBase = 'cn=schema,cn=config'
        searchFilter = '(&(objectClass=olcSchemaConfig)(cn=*))'
        attrsFilter = ['cn']

        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_ONELEVEL)
        schemas = []
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                cn_elems = string.split(values['cn'][0], ',')
                schemas.append( cn_elems[0].split('}')[1] )

        if len(schemas) > 0:
            print("Schemas: " + str(string.join(schemas, '\n         ')))
        else:
            print("Schemas: <none>")
        return 0 
