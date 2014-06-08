#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from ._backend import *
import sys
import logging
import xml.etree.ElementTree as ET

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
    
logger = logging.getLogger(__name__)

def sleekxmpp_validate_html_message(html):
    try:
        tree = ET.XML(html)
    except ET.ParseError as e:
        raise XMPPInvalidMessage(html, str(e))
    return True

def sleekxmpp_prepare_html_message(message):
    message = message.replace('&', '&amp;')
    sleekxmpp_validate_html_message(message)
    return message

class SleekXMPPBot(BackendBot):
    
    from sleekxmpp import ClientXMPP
    class ChatMsgBot(ClientXMPP):

        """
        A basic SleekXMPP bot that will log in, send a message,
        and then log out.
        """

        def __init__(self, jid, password, callback, ipv4=True, ipv6=True):
            super(SleekXMPPBot.ChatMsgBot, self).__init__(jid, password)

            self.use_ipv6 = ipv6
            # The message we wish to send, and the JID that
            # will receive it.
            self._callback = callback
            
            self._session_started = False

            # The session_start event will be triggered when
            # the bot establishes its connection with the server
            # and the XML streams are ready for use. We want to
            # listen for this event so that we we can initialize
            # our roster.
            self.add_event_handler("session_start", self.start, threaded=True)

            # The message event is triggered whenever a message
            # stanza is received. Be aware that that includes
            # MUC messages and error messages.
            self.add_event_handler("message", self.message)

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
            
            self._session_started = True
            
            logger.info('session_start')

            self._callback('session_start', None)

        def message(self, msg):
            """
            Process incoming message stanzas. Be aware that this also
            includes MUC messages and error messages. It is usually
            a good idea to check the messages's type before processing
            or sending replies.

            Arguments:
                msg -- The received message stanza. See the documentation
                    for stanza objects and the Message stanza to see
                    how it may be used.
            """
            logger.info('message')
            self._callback('message', msg)
            
        def close(self, wait=True):
            self.disconnect(wait=wait)

    def __init__(self, jid, password, callback, ipv4=True, ipv6=True):
        self._user_callback = callback
        self.xmpp = SleekXMPPBot.ChatMsgBot(jid, password, self._xmpp_callback, ipv4=ipv4, ipv6=ipv6)
        self.xmpp.register_plugin('xep_0030') # Service Discovery
        self.xmpp.register_plugin('xep_0199') # XMPP Ping
        self.xmpp.connect(use_ssl=False, use_tls=True)
        self.xmpp.process(block=False)

    def _xmpp_callback(self, eventtype, *args):
        logger.info('_xmpp_handler ' + eventtype + str(args))
        if self._user_callback is not None:
            self._user_callback(self, eventtype, args)

    def send(self, recipient, message, subject=None, html=None, message_type='chat'):
        if self.xmpp._session_started == False:
            return False
        else:
            self.xmpp.send_message(mto=recipient,
                            msubject=subject,
                            mbody=message,
                            mhtml=sleekxmpp_prepare_html_message(html) if html is not None else None,
                            mtype=message_type)
            return True

    def close(self, wait=True):
        self.xmpp.disconnect(wait=wait)


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
                              mhtml=sleekxmpp_prepare_html_message(html) if html is not None else None,
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

def sleekxmpp_message_bot(sender, password, callback=None, ipv4=True, ipv6=True):
    xmpp = SleekXMPPBot(sender, password, callback, ipv4=ipv4, ipv6=ipv6)
    
    return xmpp

def sleekxmpp_backend_info():
    from sleekxmpp.version import __version__ as version, __version_info__ as version_info
    return BackendInfo('SleekXMPP', 'SleekXMPP is an MIT licensed XMPP library for Python 2.6/3.1+', 'https://github.com/fritzy/SleekXMPP', version)
