#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .cxn import *

from arsoft.timestamp import ad_timestamp_to_datetime

AD_UF_ACCOUNTDISABLE = 0x0002
AD_UF_PASSWD_NOT_REQUIRED = 0x0020
AD_UF_PASSWD_CANT_CHANGE = 0x0040
AD_UF_NORMAL_ACCOUNT = 0x0200
AD_UF_DONT_EXPIRE_PASSWD = 0x10000
AD_UF_SMARTCARD_REQUIRED = 0x40000
AD_UF_PASSWORD_EXPIRED = 0x800000

class PasswordSettings(object):
    def __init__(self):
        self.password_properties = None
        self.password_history_len = None
        self.min_password_len = None
        self.min_password_age = None
        self.max_password_age = None
        self.lockout_duration = None
        self.lockout_threshold = None
        self.lockout_observation_window = None

    @property
    def is_password_expire_enabled(self):
        return True if self.max_password_age > 0 else False

# NIS or SFU (Services for Unix) settings
class SFUSettings(object):

    DEFAULT_MAX_GID_NUMBER = 10000
    DEFAULT_MAX_UID_NUMBER = 10000

    def __init__(self):
        self.max_gid_number = None
        self.max_uid_number = None

    @staticmethod
    def defaults():
        ret = SFUSettings()
        ret.max_gid_number = SFUSettings.DEFAULT_MAX_GID_NUMBER
        ret.max_uid_number = SFUSettings.DEFAULT_MAX_UID_NUMBER
        return ret

class ADUser(object):
    def __init__(self, name):
        self.name = name
        self.account_control = 0
        self.account_expires = None
        self.password_last_set = None
        self.password_expire = None
        self._must_change_password = False

    @property
    def uid(self):
        return self.name

    @property
    def is_disabled(self):
        return True if self.account_control & AD_UF_ACCOUNTDISABLE else False

    @property
    def password_does_not_expire(self):
        return True if self.account_control & AD_UF_DONT_EXPIRE_PASSWD else False

    @property
    def password_expired(self):
        return True if self.account_control & AD_UF_PASSWORD_EXPIRED else False

    @property
    def normal_account(self):
        return True if self.account_control & AD_UF_NORMAL_ACCOUNT else False

    @property
    def password_not_required(self):
        return True if self.account_control & AD_UF_PASSWD_NOT_REQUIRED else False

    @property
    def must_change_password(self):
        return self._must_change_password


class NoConnection(Exception):
    pass

class ActiveDirectoryDomain(object):

    def __init__(self, domain_name=None, username=None, password=None, saslmech=None, logger=None):
        self._cxn = None
        self._username = username
        self._password = password
        self._saslmech = saslmech
        self._logger = logger
        if domain_name is None:
            (fqdn, hostname, self._domain_name) = gethostname_tuple()
        else:
            self._domain_name = domain_name
        self.set_base(None)

    def __del__(self):
        if self._cxn is not None:
            self._cxn.close()

    def verbose(self, msg):
        if self._logger is not None:
            self._logger.verbose(msg)

    def error(self, msg):
        if self._logger is not None:
            self._logger.error(msg)

    def close(self):
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
        # use LDAP (with SSL) to connect to domain by default
        uri = 'ldaps://' + self._domain_name
        self.verbose('connect %s as %s (using %s)' % (uri, self._username, self._saslmech))
        self._cxn = LdapConnection(uri, self._username, self._password, self._saslmech, logger=self)
        return self._cxn.connect()

    @property
    def sfu_settings(self):
        if self._cxn is None:
            raise NoConnection

        ret = SFUSettings.defaults()
        searchBase = 'CN=%s,CN=ypservers,CN=ypServ30,CN=RpcServices,CN=System,' % self._samba_domain + self._base
        searchFilter = None
        attrsFilter = ['msSFU30MaxGidNumber', 'msSFU30MaxUidNumber']
        result = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=BASE)
        if result is not None:
            if 'msSFU30MaxGidNumber' in result[0]:
                ret.max_gid_number = int(result[0]['msSFU30MaxGidNumber'])
            if 'msSFU30MaxUidNumber' in result[0]:
                ret.max_uid_number = int(result[0]['msSFU30MaxUidNumber'])
        return ret

    @property
    def password_settings(self):
        if self._cxn is None:
            raise NoConnection

        ret = PasswordSettings()
        # from /usr/lib/python2.7/dist-packages/samba/netcmd/domain.py
        # class cmd_domain_passwordsettings(Command):
        searchBase = self._base
        searchFilter = None
        attrsFilter = ["pwdProperties", "pwdHistoryLength", "minPwdLength",
                 "minPwdAge", "maxPwdAge", "lockoutDuration", "lockoutThreshold",
                 "lockOutObservationWindow"]
        cur_max_pwd_age = 0

        res = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=BASE)
        if res is not None:
            ret.password_properties = int(res[0]["pwdProperties"][0])
            ret.password_history_len = int(res[0]["pwdHistoryLength"][0])
            ret.min_password_len = int(res[0]["minPwdLength"][0])
            # ticks -> days
            ret.min_password_age = int(abs(int(res[0]["minPwdAge"][0])) / (1e7 * 60 * 60 * 24))
            if int(res[0]["maxPwdAge"][0]) == -0x8000000000000000:
                ret.max_password_age = 0
            else:
                ret.max_password_age = int(abs(int(res[0]["maxPwdAge"][0])) / (1e7 * 60 * 60 * 24))
            ret.lockout_threshold = int(res[0]["lockoutThreshold"][0])
            # ticks -> mins
            if int(res[0]["lockoutDuration"][0]) == -0x8000000000000000:
                ret.lockout_duration = 0
            else:
                ret.lockout_duration = abs(int(res[0]["lockoutDuration"][0])) / (1e7 * 60)
            ret.lockout_observation_window = abs(int(res[0]["lockOutObservationWindow"][0])) / (1e7 * 60)

        return ret

    @property
    def users(self):
        if self._cxn is None:
            raise NoConnection

        ret = []

        searchBase = self._base
        searchFilter = '(objectClass=user)'
        attrsFilter = ['name', 'sAMAccountName', 'pwdLastSet', 'accountExpires', 'userAccountControl']
        self.verbose('Search %s (%s)' % (searchBase, searchFilter))

        result = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=SUBTREE)
        if result is not None:
            for entry in result:
                #uid = entry['name']
                #samaccountname = entry['sAMAccountName']
                uid = entry['sAMAccountName']
                useraccountcontrol = int(entry.get('userAccountControl', 0))
                pwdlastset_raw = int(entry.get('pwdLastSet', 0))
                pwdlastset = ad_timestamp_to_datetime( pwdlastset_raw )
                accountexpires = ad_timestamp_to_datetime( int(entry.get('accountExpires', 0)) )
                mailaddr = None

                user = ADUser(entry['sAMAccountName'])
                user.account_control = useraccountcontrol
                user.account_expires = accountexpires
                user.password_last_set = pwdlastset
                user._must_change_password = True if pwdlastset_raw == 0 else False
                ret.append(user)
        return ret
