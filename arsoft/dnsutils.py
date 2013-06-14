#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re
import socket
import base64
import dns
import dns.dnssec
import dns.tsigkeyring


ALGORITHM_ID_TO_NAME = {
    157: dns.tsig.HMAC_MD5,
    161: dns.tsig.HMAC_SHA1,
    162: dns.tsig.HMAC_SHA224,
    163: dns.tsig.HMAC_SHA256,
    164: dns.tsig.HMAC_SHA384,
    165: dns.tsig.HMAC_SHA512,
    }

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
    
def get_algorithm_for_number(num):
    if num in ALGORITHM_ID_TO_NAME:
        return ALGORITHM_ID_TO_NAME[num]
    else:
        return None

def read_key_file(filename):
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
        keyline = None
        ret = None
    return ret

def use_key_file(update_obj, keyfile):
    keys = read_key_file(keyfile)
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
