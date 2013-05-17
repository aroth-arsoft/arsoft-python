#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from _backend import *

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

def sleekxmpp_send_message(sender, password, recipient, body, html=None, subject=None, message_type='chat',
                           ipv4=True, ipv6=True):

    from sleekxmpp import ClientXMPP
    class SendMsgBot(ClientXMPP):

        """
        A basic SleekXMPP bot that will log in, send a message,
        and then log out.
        """

        def __init__(self, jid, password, recipient, message, html=None, subject=None, message_type='chat',
                     ipv4=True, ipv6=True):
            ClientXMPP.__init__(self, jid, password)

            self.use_ipv6 = ipv6
            # The message we wish to send, and the JID that
            # will receive it.
            self.recipient = recipient
            self.subject = subject
            self.message = message
            self.html = html
            self.message_type = message_type
            self.message_sent = False

            # The session_start event will be triggered when
            # the bot establishes its connection with the server
            # and the XML streams are ready for use. We want to
            # listen for this event so that we we can initialize
            # our roster.
            self.add_event_handler("session_start", self.start, threaded=True)

        def start(self, event):
            """
            Process the session_start event.

            Typical actions for the session_start event are
            requesting the roster and broadcasting an initial
            presence stanza.

            Arguments:
                event -- An empty dictionary. The session_start
                        event does not provide any additional
                        data.
            """
            self.send_presence()
            self.get_roster()

            self.send_message(mto=self.recipient,
                              msubject=self.subject,
                              mbody=self.message,
                              mhtml=self.html,
                              mtype=self.message_type)
            self.message_sent = True

            # Using wait=True ensures that the send queue will be
            # emptied before ending the session.
            self.disconnect(wait=True)

    xmpp = SendMsgBot(sender, password, recipient, body, html, subject, message_type, ipv4=ipv4, ipv6=ipv6)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.connect(use_ssl=False, use_tls=True)
    xmpp.process(block=True)
    return xmpp.message_sent

def sleekxmpp_message_bot(sender, password, handler=None, ipv4=True, ipv6=True):

    from sleekxmpp import ClientXMPP
    class ChatMsgBot(ClientXMPP):

        """
        A basic SleekXMPP bot that will log in, send a message,
        and then log out.
        """

        def __init__(self, jid, password, handler, ipv4=True, ipv6=True):
            ClientXMPP.__init__(self, jid, password)

            self.use_ipv6 = ipv6
            # The message we wish to send, and the JID that
            # will receive it.
            self.handler = handler

            # The session_start event will be triggered when
            # the bot establishes its connection with the server
            # and the XML streams are ready for use. We want to
            # listen for this event so that we we can initialize
            # our roster.
            self.add_event_handler("session_start", self.start, threaded=True)

        def start(self, event):
            """
            Process the session_start event.

            Typical actions for the session_start event are
            requesting the roster and broadcasting an initial
            presence stanza.

            Arguments:
                event -- An empty dictionary. The session_start
                        event does not provide any additional
                        data.
            """
            self.send_presence()
            self.get_roster()

            self.handler('session_start', None)
            
        def send(self, recipient, message, subject=None, html=None, message_type='chat'):
            self.send_message(mto=recipient,
                              msubject=subject,
                              mbody=message,
                              mhtml=html,
                              mtype=message_type)
            
        def close(self):
            self.disconnect()

    xmpp = ChatMsgBot(sender, password, handler, ipv4=ipv4, ipv6=ipv6)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.connect(use_ssl=False, use_tls=True)
    xmpp.process(block=False)
    return xmpp


def sleekxmpp_backend_info():
    from sleekxmpp.version import __version__ as version, __version_info__ as version_info
    return BackendInfo('SleekXMPP', 'SleekXMPP is an MIT licensed XMPP library for Python 2.6/3.1+', 'https://github.com/fritzy/SleekXMPP', version)
