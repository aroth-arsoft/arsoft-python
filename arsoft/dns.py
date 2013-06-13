#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import dns
import re

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
    except socket.error:
        ret = False
    return ret
#
# Is a valid IPv6 address?
def is_valid_ipv6(Address):
    try:
        dns.ipv6.inet_aton(Address) 
        ret = True
    except socket.error:
        ret = False
    return ret

def is_valid_name(Name):
    if re.match(r'^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]\.?)$', Name):
        return True
    else:
        return False

def read_key_file(filename):
    try:
        f = open(filename, 'r')
        keyline = f.readline()
        f.close()
    except IOError:
        keyline = None
    if keyline:
        k = {keyline.rsplit(' ')[0]:keyline.rsplit(' ')[6]}
        try:
            ret = dns.tsigkeyring.from_text(k)
        except:
            ret = None
    else:
        ret = None
    return ret
