#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# version of the arsoft.xmpp module
__version__ = '1.0'

from _sleekxmpp import sleekxmpp_send_message, sleekxmpp_backend_info, sleekxmpp_message_bot, sleekxmpp_validate_html_message
from _backend import daemon_send_message, XMPPInvalidMessage
from config import xmpp_config

def send_message(sender, password, recipient, body, html=None, subject=None, message_type=None,
                           ipv4=True, ipv6=True, use_daemon=False, socket_path='/run/arsoft-xmpp-daemon/socket'):
    if use_daemon:
        return daemon_send_message(sender=sender, password=password, to=recipient, body=body,
                                        html=html, subject=subject, message_type=message_type, 
                                        socket_path=socket_path)
    else:
        return sleekxmpp_send_message(sender=sender, password=password, recipient=recipient, body=body, 
                                        html=html, subject=subject, message_type=message_type if message_type else 'chat',
                                        ipv4=ipv4, ipv6=ipv6)
def backend_info():
    return sleekxmpp_backend_info()

def message_bot(sender, password, callback=None, ipv4=True, ipv6=True):
    return sleekxmpp_message_bot(sender=sender, password=password, callback=callback,
                                    ipv4=ipv4, ipv6=ipv6)
    
def validate_html_message(html):
    return sleekxmpp_validate_html_message(html)

def version():
    return __version__
