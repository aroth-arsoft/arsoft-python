#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

class mail(object):
    COMMASPACE = ', '
    
    def __init__(self, sender=None, to=[], cc=[], bcc=[], subject=None, bodytext=None, multipart=True):
        if sender is None:
            self._from = os.getlogin()
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
            self._msg['To'] = mail.COMMASPACE.join(to)
        if len(cc) != 0:
            self._msg['CC'] = mail.COMMASPACE.join(cc)
        if len(bcc) != 0:
            self._msg['BCC'] = mail.COMMASPACE.join(bcc)

    def add_attachment(self, filename, mimetype=None):
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        if mimetype is None:
            ctype, encoding = mimetypes.guess_type(filename)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
        else:
            ctype = mimetype
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            fp = open(filename)
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=subtype)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            fp.close()
            # Encode the payload using Base64
            encoders.encode_base64(msg)
        # Set the filename parameter
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
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
    m = mail(to=['root'], subject='Hello')
    s = smtplib.SMTP('localhost')
    s.sendmail(m.sender, m.recipients, str(m))
    s.quit()
