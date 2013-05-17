#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# version of the arsoft.xmpp module
__version__ = '1.0'

from _sleekxmpp import sleekxmpp_send_message, sleekxmpp_backend_info, sleekxmpp_message_bot

def send_message(sender, password, recipient, body, html=None, subject=None, message_type='chat',
                           ipv4=True, ipv6=True):
    return sleekxmpp_send_message(sender=sender, password=password, recipient=recipient, body=body, 
                                    html=html, subject=subject, message_type=message_type,
                                    ipv4=ipv4, ipv6=ipv6)
def backend_info():
    return sleekxmpp_backend_info()

def message_bot(sender, password, handler=None, ipv4=True, ipv6=True):
    return sleekxmpp_message_bot(sender=sender, password=password, handler=handler,
                                    ipv4=ipv4, ipv6=ipv6)

def version():
    return __version__
