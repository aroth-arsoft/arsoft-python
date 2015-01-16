#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
from arsoft.utils import runcmd

def xdg_open(*args, **kwargs):
    real_args = 'xdg-open'
    real_args.extend(args)
    if runcmd(real_args) == 0:
        ret = True
    else:
        ret = False
    return ret

def xdg_email(subject, body, cc=[], bcc=[], attachments=[], recipiants=[], utf8=False, uri=None, verbose=False):
    args=['xdg-email']
    if utf8:
        args.append('--utf8')
    if subject is not None:
        args.extend(['--subject', subject])
    if body is not None:
        args.extend(['--body', subject])
    if cc is not None:
        for addr in cc:
            args.extend(['--cc', addr])
    if bcc is not None:
        for addr in bcc:
            args.extend(['--bcc', addr])
    if attachments is not None:
        for a in attachments:
            args.extend(['--attach', a])
    if recipiants is not None:
        for addr in recipiants:
            args.append(addr)
    if uri is not None:
        args.append(uri)

    if runcmd(args, verbose=verbose) == 0:
        ret = True
    else:
        ret = False
    return ret
