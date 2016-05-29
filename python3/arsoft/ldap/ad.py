#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .cxn import *
import struct
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

    def __init__(self, cxn=None):
        self._max_gid_number = None
        self._max_uid_number = None
        self._cxn = cxn

    @staticmethod
    def defaults(cxn=None):
        ret = SFUSettings(cxn)
        ret._max_gid_number = SFUSettings.DEFAULT_MAX_GID_NUMBER
        ret._max_uid_number = SFUSettings.DEFAULT_MAX_UID_NUMBER
        return ret

    @property
    def max_gid_number(self):
        return self._max_gid_number

    @max_gid_number.setter
    def max_gid_number(self, value):
        self._max_gid_number = value
        if self._cxn is not None:
            self._cxn.update_sfu_settings(self)

    @property
    def max_uid_number(self):
        return self._max_uid_number

    @max_uid_number.setter
    def max_uid_number(self, value):
        self._max_uid_number = value
        if self._cxn is not None:
            self._cxn.update_sfu_settings(self)

class RIDSet(object):
    def __init__(self):
        self.allocation_pool = None
        self.next_rid = None
        self.previous_allocation_pool = None
        self.used_ool = None

class ADSamAccount(object):
    def __init__(self, name, object_sid):
        self.name = name
        self.object_sid = object_sid
        if isinstance(object_sid, bytes) and len(object_sid) > 4:
            t = struct.unpack('<L', object_sid[-4:])
            self.rid = t[0]
        else:
            self.rid = 0
    @property
    def object_sid_as_string(self):
        return str(self.rid)

    @property
    def is_builtin(self):
        return True if self.rid < 1000 else False

class ADUser(ADSamAccount):
    def __init__(self, name, object_sid):
        ADSamAccount.__init__(self, name, object_sid)
        self.uid_number = 0
        self.gid_number = 0
        self.nis_domain = None
        self.unix_home = None
        self.login_shell = None
        self.primary_gid = None
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

    def __str__(self):
        return 'ADUser(%s/%i - %s/%i)' % (self.name, self.uid_number, self.object_sid_as_string, self.rid)

class ADGroup(ADSamAccount):
    def __init__(self, name, object_sid):
        ADSamAccount.__init__(self, name, object_sid)
        self.gid_number = 0
        self.nis_domain = None
        self.members = []

    def __str__(self):
        return 'ADGroup(%s/%i - %s/%i)' % (self.name, self.gid_number, self.object_sid_as_string, self.rid)

class ADIdMap(object):
    def __init__(self, cxn):
        self._cxn = cxn
        self._users = None
        self._groups = None
        self._object_sid_map = {}
        self._uid_map = {}
        self._gid_map = {}
        self._rid_map = {}

    @property
    def groups(self):
        if self._cxn is None:
            raise NoConnection

        if self._groups is None:
            self._groups = self._cxn.groups
            for group in self._groups:
                self._object_sid_map[group.object_sid] = group
                self._rid_map[group.rid] = group
                if group.gid_number != 0:
                    self._gid_map[group.gid_number] = group
        return self._groups

    @property
    def users(self):
        if self._cxn is None:
            raise NoConnection

        if self._users is None:
            self._users = self._cxn.users
            for user in self._users:
                self._object_sid_map[user.object_sid] = user
                self._rid_map[user.rid] = user
                if user.uid_number != 0:
                    self._uid_map[user.uid_number] = user
        return self._users

    def get_group_by_rid(self, rid):
        if self._groups is None:
            self.groups
        if rid in self._rid_map:
            ret = self._rid_map[rid]
            if isinstance(ret, ADGroup):
                return ret
        return None

    def get_user_by_rid(self, rid):
        if self._users is None:
            self.users
        if rid in self._rid_map:
            ret = self._rid_map[rid]
            if isinstance(ret, ADUser):
                return ret
        return None

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
        self.set_domain(None)

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

        ret = SFUSettings.defaults(self)
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

    def update_sfu_settings(self, sfu):
        if self._cxn is None:
            raise NoConnection
        print('update_sfu_settings')
        dn = 'CN=%s,CN=ypservers,CN=ypServ30,CN=RpcServices,CN=System,' % self._samba_domain + self._base
        changes = {
            'msSFU30MaxGidNumber': [ (ldap3.MODIFY_REPLACE, [ sfu.max_gid_number ] ) ],
            'msSFU30MaxUidNumber': [ (ldap3.MODIFY_REPLACE, [ sfu.max_uid_number ] ) ],
            }
        self._cxn.modify(dn, changes)

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
    def rid_set(self):
        if self._cxn is None:
            raise NoConnection

        domain_controller = 'OSSRV'
        ret = RIDSet()
        searchBase = 'CN=RID Set,CN=%s,OU=Domain Controllers,' % domain_controller + self._base
        searchFilter = None
        attrsFilter = ["rIDAllocationPool", "rIDNextRID", "rIDPreviousAllocationPool", 'rIDUsedPool' ]
        res = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=BASE)
        if res is not None:
            ret.allocation_pool = int(res[0]["rIDAllocationPool"][0])
            ret.next_rid = int(res[0]["rIDNextRID"][0])
            ret.previous_allocation_pool = int(res[0]["rIDPreviousAllocationPool"][0])
            ret.used_ool = int(res[0]["rIDUsedPool"][0])
        return ret

    @property
    def users(self):
        if self._cxn is None:
            raise NoConnection

        ret = []

        searchBase = self._base
        searchFilter = '(objectClass=user)'
        attrsFilter = ['name', 'sAMAccountName', 'pwdLastSet', 'accountExpires', 'userAccountControl',
                       'objectSid',
                       'userPrincipalName', 'displayName', 'primaryGroupID', 'memberOf',
                       'unixHomeDirectory', 'loginShell', 'uidNumber', 'gidNumber', 'msSFU30NisDomain'  ]
        self.verbose('Search %s (%s)' % (searchBase, searchFilter))

        result = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=SUBTREE)
        if result is not None:
            for entry in result:
                entry_attrs = entry.entry_get_attribute_names()
                useraccountcontrol = int(entry.get('userAccountControl', 0))
                pwdlastset_raw = int(entry.get('pwdLastSet', 0))
                pwdlastset = ad_timestamp_to_datetime( pwdlastset_raw )
                accountexpires = ad_timestamp_to_datetime( int(entry.get('accountExpires', 0)) )
                mailaddr = None

                user = ADUser(entry['sAMAccountName'].value, entry['objectSid'].value)
                user.account_control = useraccountcontrol
                user.account_expires = accountexpires
                user.password_last_set = pwdlastset
                user._must_change_password = True if pwdlastset_raw == 0 else False

                user.primary_gid = int(entry['primaryGroupID'].value) if 'primaryGroupID' in entry_attrs else 0
                user.uid_number = int(entry['uidNumber'].value) if 'uidNumber' in entry_attrs else 0
                user.gid_number = int(entry['gidNumber'].value) if 'gidNumber' in entry_attrs else 0
                user.nis_domain = str(entry['msSFU30NisDomain'].value) if 'msSFU30NisDomain' in entry_attrs else None
                user.unix_home = int(entry['unixHomeDirectory'].value) if 'unixHomeDirectory' in entry_attrs else None
                user.login_shell = int(entry['loginShell'].value) if 'loginShell' in entry_attrs else None

                ret.append(user)
        return ret

    @property
    def groups(self):
        if self._cxn is None:
            raise NoConnection

        ret = []

        searchBase = self._base
        searchFilter = '(objectClass=group)'
        attrsFilter = ['name', 'sAMAccountName', 'member', 'gidNumber', 'objectSid', 'msSFU30NisDomain'  ]
        self.verbose('Search %s (%s)' % (searchBase, searchFilter))

        result = self._cxn.search(searchBase, searchFilter, attrsFilter, scope=SUBTREE)
        if result is not None:
            for entry in result:
                entry_attrs = entry.entry_get_attribute_names()

                useraccountcontrol = int(entry.get('userAccountControl', 0))
                pwdlastset_raw = int(entry.get('pwdLastSet', 0))
                pwdlastset = ad_timestamp_to_datetime( pwdlastset_raw )
                accountexpires = ad_timestamp_to_datetime( int(entry.get('accountExpires', 0)) )
                mailaddr = None

                group = ADGroup(entry['sAMAccountName'].value, entry['objectSid'].value)
                if 'member' in entry_attrs:
                    group.members = entry['member']
                group.nis_domain = str(entry['msSFU30NisDomain'].value) if 'msSFU30NisDomain' in entry_attrs else None
                group.gid_number = int(entry['gidNumber'].value) if 'gidNumber' in entry_attrs else 0

                ret.append(group)
        return ret

    @property
    def idmap(self):
        if self._cxn is None:
            raise NoConnection

        return ADIdMap(self)

