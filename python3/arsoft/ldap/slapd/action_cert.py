#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import ldap
import ldap.modlist as modlist
from action_base import *

class action_cert(action_base):

    def __init__(self, app, args):
        action_base.__init__(self, app, args)

    def run(self):
        searchBase = 'cn=config'
        searchFilter = '(cn=config)'
        attrsFilter = ['olcTLSCACertificateFile', 'olcTLSCACertificatePath', 'olcTLSCRLFile', 'olcTLSCertificateFile', 'olcTLSCertificateKeyFile',
                        'olcTLSCRLCheck', 'olcTLSCipherSuite', 'olcTLSDHParamFile', 'olcTLSRandFile', 'olcTLSVerifyClient']

        result_set = self._search(searchBase, searchFilter, attrsFilter, ldap.SCOPE_BASE)
        tls_cipher_suite = None
        tls_cacert_file = None
        tls_cacert_path = None
        tls_crl_file = None
        tls_crl_check = None
        tls_cert_file = None
        tls_key_file = None
        tls_dhparam_file = None
        tls_rand_file = None
        tls_verify_client = None
        if result_set is not None:
            for rec in result_set:
                (dn, values) = rec[0]
                tls_cipher_suite = values['olcTLSCipherSuite'][0] if 'olcTLSCipherSuite' in values else None
                tls_cacert_file = values['olcTLSCACertificateFile'][0] if 'olcTLSCACertificateFile' in values else None
                tls_cacert_path = values['olcTLSCACertificatePath'][0] if 'olcTLSCACertificatePath' in values else None
                tls_crl_file = values['olcTLSCRLFile'][0] if 'olcTLSCRLFile' in values else None
                tls_crl_check = values['olcTLSCRLCheck'][0] if 'olcTLSCRLCheck' in values else None
                tls_cert_file = values['olcTLSCertificateFile'][0] if 'olcTLSCertificateFile' in values else None
                tls_key_file = values['olcTLSCertificateKeyFile'][0] if 'olcTLSCertificateKeyFile' in values else None
                tls_dhparam_file = values['olcTLSDHParamFile'][0] if 'olcTLSDHParamFile' in values else None
                tls_rand_file = values['olcTLSRandFile'][0] if 'olcTLSRandFile' in values else None
                tls_verify_client = values['olcTLSVerifyClient'][0] if 'olcTLSVerifyClient' in values else None

        print("TLS cipher suite:        " + (tls_cipher_suite if tls_cipher_suite is not None else '<none>'))
        print("TLS CA certificate file: " + (tls_cacert_file if tls_cacert_file is not None else '<none>'))
        print("TLS CA certificate path: " + (tls_cacert_path if tls_cacert_path is not None else '<none>'))
        print("TLS CRL file:            " + (tls_crl_file if tls_crl_file is not None else '<none>'))
        print("TLS CRL check:           " + (tls_crl_check if tls_crl_check is not None else '<none>'))
        print("TLS certificate file:    " + (tls_cert_file if tls_cert_file is not None else '<none>'))
        print("TLS key file:            " + (tls_key_file if tls_key_file is not None else '<none>'))
        print("TLS DH param file:       " + (tls_dhparam_file if tls_dhparam_file is not None else '<none>'))
        print("TLS rand file:           " + (tls_rand_file if tls_rand_file is not None else '<none>'))
        print("TLS verify client:       " + (tls_verify_client if tls_verify_client is not None else '<none>'))
        return 0
