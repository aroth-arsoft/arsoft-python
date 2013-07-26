#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re
import socket
import base64
import arsoft.inifile
import dns
import dns.dnssec
import dns.tsigkeyring
import dns.resolver
import dns.rdtypes
import dns.rdtypes.IN.A
import dns.rdtypes.IN.AAAA
from arsoft.utils import enum

ALGORITHM_ID_TO_NAME = {
    157: dns.tsig.HMAC_MD5,
    161: dns.tsig.HMAC_SHA1,
    162: dns.tsig.HMAC_SHA224,
    163: dns.tsig.HMAC_SHA256,
    164: dns.tsig.HMAC_SHA384,
    165: dns.tsig.HMAC_SHA512,
    }

ALGORITHM_NAME_TO_ID = {v:k for k, v in ALGORITHM_ID_TO_NAME.items()}

def get_algorithm_for_number(num):
    if num in ALGORITHM_ID_TO_NAME:
        return ALGORITHM_ID_TO_NAME[num]
    else:
        return None

def get_algorithm_for_name(name):
    dns_name = dns.name.from_text(name)
    if dns_name in ALGORITHM_NAME_TO_ID:
        return ALGORITHM_NAME_TO_ID[dns_name]
    else:
        return None

KeyFileFormat = enum(Automatic=-2, Invalid=-1, Zone=0, TSIG=1, Private=2)

#
# Is a valid TTL?
def is_valid_ttl(TTL):
    try:
        TTL = dns.ttl.from_text(TTL)
        ret = True
    except:
        ret = False
    return ret
#
# Is a Valid PTR?
def is_valid_ptr(ptr):
    if re.match(r'\b(?:\d{1,3}\.){3}\d{1,3}.in-addr.arpa\b', ptr):
        return True
    else:
        return False
#
# Is a valid IPV4 address?
def is_valid_ipv4(Address):
    try:
        dns.ipv4.inet_aton(Address)
        ret = True
    except (socket.error, dns.exception.SyntaxError):
        ret = False
    return ret
#
# Is a valid IPv6 address?
def is_valid_ipv6(Address):
    try:
        dns.ipv6.inet_aton(Address) 
        ret = True
    except (socket.error, dns.exception.SyntaxError):
        ret = False
    return ret

def is_valid_name(Name):
    if re.match(r'^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]\.?)$', Name):
        return True
    else:
        return False

def _read_key_file_zone(filename):
    try:
        ret = {}
        f = open(filename, 'r')
        for line in f:
            keyline = line.strip()
            #print('keyline %s' % keyline)
            keyline_elems = keyline.rsplit(' ')
            keyprotocol = int(keyline_elems[4])
            keyalgorithm = get_algorithm_for_number(int(keyline_elems[5]))
            keyname = dns.name.from_text(keyline_elems[0])
            secret = base64.decodestring(''.join(keyline_elems[6:]))
            ret[keyname] = {'secret': secret, 'protocol':keyprotocol, 'algorithm':keyalgorithm }
        f.close()
    except IOError:
        ret = None
    return ret

def _read_key_file_tsig(filename):
    """Accept a TSIG keyfile and a key name to retrieve.
    Return a keyring object with the key name and TSIG secret."""

    if hasattr(filename, 'read'):
        key_struct = filename.read()
    else:
        try:
            f = open(filename, 'r')
            key_struct = f.read()
            f.close()
        except IOError:
            key_struct = None

    if key_struct:
        try:
            key_data = re.search(r"key \"%s\" \{(.*?)\}\;" % key_name, key_struct, re.DOTALL).group(1)
            algorithm = re.search(r"algorithm ([a-zA-Z0-9_-]+?)\;", key_data, re.DOTALL).group(1)
            tsig_secret = re.search(r"secret \"(.*?)\"", key_data, re.DOTALL).group(1)
        except AttributeError:
            keyname = None
            raise

        if keyname:
            keyprotocol = get_algorithm_for_name(keyalgorithm)
            ret = {}
            ret[keyname] = {'secret': secret, 'protocol':keyprotocol, 'algorithm':keyalgorithm }
        else:
            ret = None
    else:
        ret = None
    return ret

def _read_key_data_zone(data):
    ret = {}
    for line in data.splitlines():
        keyline = line.strip()
        #print('keyline %s' % keyline)
        keyline_elems = keyline.rsplit(' ')
        try:
            keyprotocol = int(keyline_elems[4])
            keyalgorithm = get_algorithm_for_number(int(keyline_elems[5]))
            keyname = dns.name.from_text(keyline_elems[0])
            secret = base64.decodestring(''.join(keyline_elems[6:]))
            ret[keyname] = {'secret': secret, 'protocol':keyprotocol, 'algorithm':keyalgorithm }
        except IndexError:
            ret = None
            break
    return ret

def _read_key_data_tsig(data):
    """Accept a TSIG keyfile and a key name to retrieve.
    Return a keyring object with the key name and TSIG secret."""
    try:
        m = re.search(r"key \"([a-zA-Z0-9_-]+?)\" \{(.*?)\}\;", data, re.DOTALL)
        keyname = m.group(1)
        key_data = m.group(2)
        keyalgorithm = re.search(r"algorithm ([a-zA-Z0-9_-]+?)\;", key_data, re.DOTALL).group(1)
        secret = re.search(r"secret \"(.*?)\"", key_data, re.DOTALL).group(1)
    except AttributeError:
        keyname = None
        raise

    if keyname:
        keyprotocol = get_algorithm_for_name(keyalgorithm)
        ret = {}
        ret[keyname] = {'secret': secret, 'protocol':keyprotocol, 'algorithm':keyalgorithm }
    else:
        ret = None
    return ret

def _read_key_file_private(filename, keyname=None):
    if keyname is None:
        if not hasattr(filename, 'read'):
            basename = os.path.basename(filename)
            if basename[0] == 'K':
                (basename, ext) = os.path.splitext(basename[1:])
                (keyname, keyprotocol, keyid) = basename.split('+', 2)

    f = arsoft.inifile.IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False, keyIsWord=False)
    if f.open(filename):
        keyalgorithm_raw = f.get(None, 'Algorithm', None)
        secret = f.get(None, 'Key', None)
        if keyalgorithm_raw:
            (keyprotocol_str, keyalgorithm) = keyalgorithm_raw.split(' ', 1)
            keyprotocol = int(keyprotocol_str)
        ret = {}
        ret[keyname] = {'secret': secret, 'protocol':keyprotocol, 'algorithm':keyalgorithm }
    else:
        ret = None
    return ret

def read_key_file(filename, format=KeyFileFormat.Zone):
    if format == KeyFileFormat.Automatic:
        if hasattr(filename, 'read'):
            keydata = filename.read()
        else:
            try:
                f = open(filename, 'r')
                keydata = f.read()
                f.close()
            except IOError:
                keydata = None
        ret = None
        if keydata is not None:
            if ret is None:
                ret = _read_key_data_zone(keydata)
            if ret is None:
                ret = _read_key_data_tsig(keydata)
        return ret
    if format == KeyFileFormat.Zone:
        return _read_key_file_zone(filename)
    elif format == KeyFileFormat.TSIG:
        return _read_key_file_tsig(filename)
    elif format == KeyFileFormat.Private:
        return _read_key_file_private(filename)
    else:
        return None

def use_key_file(update_obj, keyfile, format=KeyFileFormat.Zone):
    keys = read_key_file(keyfile, format)
    if keys:
        keyalgorithm = None
        first_keyname = None
        keyring = {}
        for (keyname, keydata) in keys.iteritems():
            if keyalgorithm is None:
                keyalgorithm = keydata['algorithm']
            if first_keyname  is None:
                first_keyname = keyname
            keyring[keyname] = keydata['secret']
            
        update_obj.keyalgorithm = keyalgorithm
        update_obj.keyname = first_keyname
        update_obj.keyring = keyring
        ret = True
    else:
        ret = False
    return ret

def gethostname_tuple(fqdn=None):
    if fqdn is None:
        fqdn = socket.getfqdn().lower()
    else:
        fqdn = fqdn.lower()
    if '.' in fqdn:
        (hostname, domain) = fqdn.split('.', 1)
    else:
        hostname = fqdn
        domain = 'localdomain'
    return (fqdn, hostname, domain)

def gethostname(fqdn=True):
    ret = socket.getfqdn()
    if not fqdn:
        if '.' in ret:
            (ret, domain) = ret.split('.', 1)
    return ret

def getdomainname():
    fqdn = socket.getfqdn()
    if '.' in fqdn:
        (hostname, ret) = fqdn.split('.', 1)
    else:
        ret = 'localdomain'
    return ret

def _get_resolver(dnsserver=None):
    if dnsserver is not None:
        nameservers = []
        if not isinstance(dnsserver, list):
            dnsserver = [dnsserver]
        for srv in dnsserver:
            if is_valid_ipv4(srv) or is_valid_ipv6(srv):
                nameservers.append(srv)
            else:
                try:
                    addr = socket.gethostbyname(srv)
                except socket.gaierror:
                    addr = None
                if addr:
                    nameservers.append(addr)
        if len(nameservers) == 0:
            ret = None
        else:
            ret = dns.resolver.Resolver()
            ret.nameservers = nameservers
    else:
       ret = dns.resolver.Resolver()
    return ret

def get_dns_srv_record(service, domain=None, default_value=None, tcp=True, dnsserver=None):
    if domain is None:
        domain = getdomainname()
    query = '_%s.%s.%s.' % (service.lower(), '_tcp' if tcp else '_udp', domain)
    resolver = _get_resolver(dnsserver)
    if resolver:
        ret = []
        answers = resolver.query(query, 'SRV')
        for rdata in answers:
            ret.append( ( rdata.target.to_text(omit_final_dot=True), rdata.port ) )
    else:
        ret = None
    return ret

def get_dns_host_record(query=None, hostname=None, domain=None, default_value=None, ipv6=False, dnsserver=None):
    if query is None:
        (local_fqdn, local_hostname, local_domain) = gethostname_tuple()
        if domain is None:
            domain = local_domain
        if hostname is None:
            hostname = local_hostname
        query = '%s.%s.' % (hostname.lower(), domain)
    resolver = _get_resolver(dnsserver)
    if resolver:
        ret = []
        answers = resolver.query(query, 'AAAA' if ipv6 else 'A')
        for rdata in answers:
            if isinstance(rdata, dns.rdtypes.IN.A.A):
                if not ipv6:
                    ret.append( rdata.address )
            elif isinstance(rdata, dns.rdtypes.IN.AAAA.AAAA):
                if ipv6:
                    ret.append( rdata.address )
    else:
        ret = None
    return ret
