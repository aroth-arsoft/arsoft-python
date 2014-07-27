#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import json
import struct
import random
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

class XMPPException(Exception):
    def __init__(self):
        pass

class XMPPInvalidMessage(XMPPException):
    def __init__(self, html, parser_error):
        self._html = html
        self._parser_error = parser_error

    def __str__(self):
        return 'XMPPInvalidMessage(%s, %s)' % (self._html, self._parser_error)

class XMPPDaemonError(XMPPException):
    def __init__(self, message_id, error_message):
        self._message_id = message_id
        self._error_message = error_message

    def __str__(self):
        return 'XMPPDaemonError(id=%i, %s)' % (self._message_id, self._error_message)

def daemon_send_message(sender=None, password=None, to=None, cc=None, body=None, html=None, subject=None, message_type=None, socket_path='/run/arsoft-xmpp-daemon/socket'):
    msg_obj = {}
    msg_obj['messageid'] = random.randint(1, 2**32)
    if sender:
        msg_obj['from'] = sender
    if to:
        msg_obj['to'] = to
    if cc:
        msg_obj['cc'] = cc
    if html is not None and len(html) > 0:
        msg_obj['body'] = html
        msg_obj['xml'] = True
    elif body is not None:
        msg_obj['body'] = body
    if subject:
        msg_obj['subject'] = subject
    if message_type:
        msg_obj['message_type'] = message_type
    arsoft_xmpp_daemon_magic = 0x87633bba
    msg = json.dumps(msg_obj) + '\n'
    print(msg)
    header = struct.pack("@I", arsoft_xmpp_daemon_magic) + struct.pack(">I", len(msg))
    resp = send_and_recv_unix_socket_message(socket_path,header + msg)
    ret = False
    if resp:
        resp_obj = json.loads(resp[8:])
        print(resp_obj)
        if int(resp_obj['messageid']) == msg_obj['messageid']:
            ret = True if resp_obj['success'] == 'true' else False
            if not ret:
                raise XMPPDaemonError(msg_obj['messageid'], resp_obj['message'])
    return ret
