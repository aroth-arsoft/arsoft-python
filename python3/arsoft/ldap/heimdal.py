#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class HeimdalUser(object):
    def __init__(self, name):
        self.name = name
        self.principal_name = None
        self.samba_account_flags = 0
        self.account_expires = None
        self.password_last_set = None

    @property
    def uid(self):
        return self.name

    @property
    def is_disabled(self):
        return True if 'D' in self.samba_account_flags else False

    @property
    def password_does_not_expire(self):
        return True if 'X' in self.samba_account_flags else False

    @property
    def password_expired(self):
        return False

    @property
    def normal_account(self):
        return True if 'U' in self.samba_account_flags else False

    @property
    def password_not_required(self):
        return True if 'N' in self.samba_account_flags else False

    @property
    def must_change_password(self):
        return False


class HeimdalDomain(object):


    def __init__(self, domain_name=None, username=None, password=None, saslmech=None):
        self._cxn = None
        self._username = username
        self._password = password
        self._saslmech = saslmech
        if domain_name is None:
            (fqdn, hostname, self._domain_name) = gethostname_tuple()
        else:
            self._domain_name = domain_name
        self.set_base(None)

    def __del__(self):
        if self._cxn is not None:
            self._cxn.close()

    def set_domain(self, domain):
        if domain is None:
            self._samba_domain = self._domain_name
        else:
            self._samba_domain = domain
        if '.' in self._samba_domain:
            self._samba_domain = self._samba_domain[0:self._samba_domain.find('.')]

    def set_base(self, base):
        if base is None:
            if '.' in self._domain_name:
                self._base = ''
                for e in self._domain_name.split('.'):
                    if self._base:
                        self._base = self._base + ',DC=' + e
                    else:
                        self._base = 'DC=' + e
            else:
                self._base = 'DC=' + self._domain_name
        else:
            self._base = base

    def connect(self):
        self._cxn = LdapConnection(uri, self._username, self._password, self._saslmech, logger=self)
        return self._cxn.connect()

    @propery
    def users(self):
        if self._cxn is None:
            raise NoConnection

        ret = []

        searchBase = self._base
        searchFilter = '(&(objectClass=krb5KDCEntry)(krb5PasswordEnd=*))'
        attrsFilter = ['uid', 'krb5PrincipalName','krb5PasswordEnd', 'mail', 'sambaAcctFlags']

        result = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=ad_password_expire.SUBTREE)
        if result is not None:
            for entry in result:
                uid = entry['uid']
                princ = entry['krb5PrincipalName']
                mailaddr = None

                if 'krb5PasswordEnd' in entry:
                    pwend = parse_date(entry['krb5PasswordEnd'][0])
                else:
                    pwend = None
                if 'mail' in entry:
                    mailaddr = entry['mail'][0]
                else:
                    mailaddr = None
                if 'sambaAcctFlags' in entry:
                    sambaAcctFlags = entry['sambaAcctFlags'][0]
                else:
                    sambaAcctFlags = ''

                user = HeimdalUser(uid)
                user.principal_name = princ
                user.samba_account_flags = sambaAcctFlags
                user.password_end = pwend
                ret.append(user)
        return ret


