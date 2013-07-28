#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import arsoft.utils
import email.encoders
import smtplib
import os

class Mail(object):
    COMMASPACE = ', '
    
    def __init__(self, sender=None, to=[], cc=[], bcc=[], subject=None, bodytext=None, multipart=True):
        if sender is None:
            self._from = arsoft.utils.getlogin()
        else:
            self._from = sender
        self._to = to
        self._cc = cc
        self._bcc = bcc
        self._subject = subject
        self._bodytext = bodytext
        self._bodymsg = MIMEText(bodytext)
        if multipart:
            self._msg = MIMEMultipart()
            self._msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'
            self._msg.attach(self._bodymsg)
        else:
            self._msg = self._bodymsg

        self._msg['Subject'] = subject
        self._msg['From'] = self._from
        if len(to) != 0:
            self._msg['To'] = Mail.COMMASPACE.join(to)
        if len(cc) != 0:
            self._msg['CC'] = Mail.COMMASPACE.join(cc)
        if len(bcc) != 0:
            self._msg['BCC'] = Mail.COMMASPACE.join(bcc)

    def add_attachment(self, filename, mimetype=None, attachment_name=None):
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        if mimetype is None:
            ctype = 'application/octet-stream'
        else:
            ctype = mimetype
        maintype, subtype = ctype.split('/', 1)
        if hasattr(filename, 'read'):
            fp = filename
        else:
            fp = open(filename)
        if maintype == 'text':
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            # Encode the payload using Base64
            email.encoders.encode_base64(msg)
        if not hasattr(filename, 'read'):
            fp.close()
        # Set the filename parameter
        if attachment_name is None:
            if not hasattr(filename, 'read'):
                attachment = os.path.basename(filename)
            else:
                attachment = os.path.basename(filename.name)
        else:
            attachment = attachment_name
        msg.add_header('Content-Disposition', 'attachment', filename=attachment)
        self._msg.attach(msg)
        
    def __str__(self):
        return self._msg.as_string()

    @property
    def sender(self):
        return self._from

    @property
    def recipients(self):
        ret = []
        ret.extend(self._to)
        ret.extend(self._cc)
        ret.extend(self._bcc)
        return ret

if __name__ == '__main__':
    m = Mail(to=['root'], subject='Hello')
    s = smtplib.SMTP('localhost')
    s.sendmail(m.sender, m.recipients, str(m))
    s.quit()
