#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

def get_full_ldap_uri(uri):
    if uri.startswith('ldap://') or \
        uri.startswith('ldaps://') or \
        uri.startswith('ldapi://'):
            pass
    else:
        if uri[0] == '/':
            uri = "ldapi://" + str(uri)
        else:
            uri = "ldap://" + str(uri)
    return uri

