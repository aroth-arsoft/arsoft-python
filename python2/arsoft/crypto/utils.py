#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import time
import os.path
from .cert import CertificateFile
from .crl import CRLFile
from arsoft.timestamp import timestamp_from_datetime, format_timedelta

def _saveint(v):
    if v is None:
        return 0
    try:
        return int(v)
    except ValueError:
        return 0

def _get_cert_min_expire(cert):
    ret = 0
    min_expire_date = None
    min_expire_subject = None
    min_expire_issuer = None
    if cert is not None and cert.valid:
        for cert_item in cert.certificates:
            if min_expire_date is None or (cert_item.expire_date < min_expire_date):
                min_expire_date = cert_item.expire_date
                min_expire_subject = cert_item.subject.commonName
                min_expire_issuer = cert_item.issuer.commonName
    if min_expire_subject and min_expire_date:
        return (min_expire_subject, min_expire_issuer, timestamp_from_datetime(min_expire_date))
    else:
        return (None, None, None)

def _get_crl_min_update(crl):
    ret = 0
    min_last_update_date = None
    min_next_update_date = None
    if crl is not None and crl.valid:
        for crl_item in crl.crls:
            if crl_item.last_update is not None and (min_last_update_date is None or (crl_item.last_update < min_last_update_date)):
                min_last_update_date = crl_item.last_update

            if crl_item.next_update is not None and (min_next_update_date is None or (crl_item.next_update < min_next_update_date)):
                min_next_update_date = crl_item.nex_update

    return (min_last_update_date, min_next_update_date)

def check_mk_cert_file_info(cert_file, prefix=None, name=None, ca=False):
    subject = None
    if cert_file is None:
        pass
    elif isinstance(cert_file, CertificateFile):
        (subject, issuer, expire_date) = _get_cert_min_expire(cert_file)
    elif os.path.isfile(cert_file):
        cert = CertificateFile(cert_file)
        (subject, issuer, expire_date) = _get_cert_min_expire(cert)
    if subject is not None:
        itemname = 'ca_expire' if ca else 'cert_expire'
        if name:
            itemname = itemname + '_' + name
        if prefix:
            itemname = prefix + ';' + itemname
        print('%s;%s;%s;%i' % (itemname, str(subject), str(issuer), expire_date))

def check_mk_crl_file_info(crl_file, prefix=None, name=None):
    min_last_update_date = None
    min_next_update_date = None
    if crl_file is None:
        pass
    elif isinstance(crl_file, CRLFile):
        (min_last_update_date, min_next_update_date) = _get_crl_min_update(crl_file)
    elif os.path.isfile(crl_file):
        crl = CRLFile(crl_file)
        (min_last_update_date, min_next_update_date) = _get_crl_min_update(crl)
    if min_last_update_date or min_next_update_date:
        itemname = 'crl_update'
        if name:
            itemname = itemname + '_' + name
        if prefix:
            itemname = prefix + ';' + itemname
        print('%s;%i;%i' % (itemname,
                            timestamp_from_datetime(min_last_update_date) if min_last_update_date else 0,
                            timestamp_from_datetime(min_next_update_date) if min_next_update_date else 0))

def check_mk_cert_inventory(checkname, info, prefix=False, warn_time=30, crit_time=14):
    ret = []
    line_item_count = 4 if not prefix else 5
    for line in info:
        if len(line) < line_item_count:
            continue

        if not prefix:
            itemname, subject, issuer, expire_date = line[0:4]
        else:
            prefix_str, itemname, subject, issuer, expire_date = line[0:5]
        if 'cert_expire' in itemname:
            ret.append( ('cert' if not prefix else prefix_str + ' cert', (warn_time, crit_time) ) )
        elif 'ca_expire' in itemname:
            ret.append( ('ca' if not prefix else prefix_str + ' ca', (warn_time, crit_time) ) )
        elif 'crl_update' in itemname:
            ret.append( ('crl' if not prefix else prefix_str + ' crl', (warn_time, crit_time) ) )
    return ret

def check_mk_cert_check_impl(itemname, params, subject, issuer, expire_date, ca=False):
    now = time.time()
    (warn_time_days, crit_time_days) = params
    warn_time = now + (warn_time_days * 86400)
    crit_time = now + (crit_time_days * 86400)
    level = 0
    perfdata = [ (itemname, int(expire_date - now)/86400 if expire_date else 0, warn_time_days, crit_time_days) ]
    if expire_date <= now:
        level = 2
        msg = 'CRIT - %sCertificate %s expired %s' % ('CA ' if ca else '', subject, format_timedelta(expire_date - now))
    elif expire_date <= warn_time:
        level = 1
        msg = 'WARN - %sCertificate %s expires in %s' % ('CA ' if ca else '', subject, format_timedelta(expire_date - now))
    elif expire_date <= crit_time:
        level = 2
        msg = 'CRIT - %sCertificate %s expires in %s' % ('CA ' if ca else '', subject, format_timedelta(expire_date - now))
    else:
        msg = 'OK - %sCertificate %s expires in %s' % ('CA ' if ca else '', subject, format_timedelta(expire_date - now))

    return (level, msg, perfdata)

def check_mk_cert_check(item, params, info, prefix=False):
    if prefix:
        prefix_item, itemtype = item.split(' ', 1)
    else:
        prefix_item, itemtype = None, item
    if itemtype == 'cert' or itemtype == 'ca':
        line_item_count = 4 if not prefix else 5
    elif itemtype == 'crl':
        line_item_count = 2 if not prefix else 3
    else:
        line_item_count = 2 if not prefix else 3

    level = 3
    msg = 'UNKNOWN - %s' % item
    perfdata = []
    for line in info:
        if len(line) < line_item_count:
            continue

        if prefix and prefix_item != line[0]:
            continue

        itemname = line[0] if not prefix else line[1]
        if itemtype == 'cert':
            if not 'cert_expire' in itemname:
                continue
            subject, issuer, expire_date = line[1:4] if not prefix else line[2:5]
            (level, msg, perfdata) = check_mk_cert_check_impl(itemname, params, subject, issuer, _saveint(expire_date))
        elif itemtype == 'ca':
            if not 'ca_expire' in itemname:
                continue
            subject, issuer, expire_date = line[1:4] if not prefix else line[2:5]
            (level, msg, perfdata) = check_mk_cert_check_impl(itemname, params, subject, issuer, _saveint(expire_date))
        elif itemtype == 'crl':
            if not 'crl_update' in itemname:
                continue
            last_update_date, next_update_data = line[1:3] if not prefix else line[2:4]
            last_update_date = _saveint(last_update_date)
            next_update_data = _saveint(next_update_data)
    return (level, msg, perfdata)
