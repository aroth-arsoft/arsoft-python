#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import json
import struct
from arsoft.socket_utils import *

class BackendInfo(object):
    def __init__(self, module_name, module_description, module_homepage, module_version):
        self.name = module_name
        self.description = module_description
        self.homepage = module_homepage
        self.version = module_version

    def __str__(self):
        ret = str(self.name) + ': ' + str(self.description) + '\n'
        if self.homepage is not None:
            ret = ret + 'Homepage: ' + str(self.homepage) + '\n'
        ret = ret + 'Version: ' + str(self.version) + '\n'
        return ret

class BackendBot(object):
    def __init__(self):
        pass
    
    def send_msg_json(self, msg):
        msg_obj = json.loads(msg)
        recipient = str(msg_obj['recipient']) if 'recipient' in msg_obj else None
        body = str(msg_obj['body']) if 'body' in msg_obj else None
        subject = str(msg_obj['subject']) if 'subject' in msg_obj else None
        html = str(msg_obj['html']) if 'html' in msg_obj else None
        if recipient:
            ret = self.send(recipient=recipient, message=body, subject=subject, html=html)
        else:
            ret = False
        return ret

class XMPPInvalidMessage(Exception):
    def __init__(self, html, parser_error):
        self._html = html
        self._parser_error = parser_error

    def __str__(self):
        return 'XMPPInvalidMessage(%s, %s)' % (self._html, self._parser_error)

def daemon_send_message(sender=None, password=None, to=None, cc=None, body=None, html=None, subject=None, message_type=None, socket_path='/run/arsoft-xmpp-daemon/socket'):
    msg_obj = {}
    if sender:
        msg_obj['from'] = sender
    if to:
        msg_obj['to'] = to
    if cc:
        msg_obj['cc'] = cc
    if html is not None and len(html) > 0:
        msg_obj['html'] = html
    elif body is not None:
        msg_obj['body'] = body
    if subject:
        msg_obj['subject'] = subject
    if message_type:
        msg_obj['message_type'] = message_type
    arsoft_xmpp_daemon_magic = 0x87633bba
    msg = json.dumps(msg_obj) + '\n'
    header = struct.pack("@I", arsoft_xmpp_daemon_magic) + struct.pack(">I", len(msg))
    if send_unix_socket_message(socket_path,header + msg) == len(header) + len(msg):
        return True
    else:
        return False
