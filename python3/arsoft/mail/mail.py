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
        self._msg = None
        if sender is None:
            self._from = arsoft.utils.getlogin()
        else:
            self._from = sender
        self._to = to if to is not None else []
        self._cc = cc if cc is not None else []
        self._bcc = bcc if bcc is not None else []
        self._subject = subject
        self._multipart = multipart
        self._bodytext = bodytext
        self._attachments = []
        
    class Attachment(object):
        def __init__(self, filename, mimetype=None, attachment_name=None):
            self._msg = None
            self.filename = filename
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
            if mimetype is None:
                self.mimetype = 'application/octet-stream'
            else:
                self.mimetype = mimetype
            self.mimetype_main, self.mimetype_sub = self.mimetype.split('/', 1)
            # Set the filename parameter
            if attachment_name is None:
                if not hasattr(filename, 'read'):
                    self.name = os.path.basename(filename)
                else:
                    self.name = os.path.basename(filename.name)
            else:
                self.name = attachment_name

        def prepare(self):
            if self._msg is None:
                if hasattr(self.filename, 'read'):
                    fp = self.filename
                else:
                    fp = open(self.filename)
                if self.mimetype_main == 'text':
                    # Note: we should handle calculating the charset
                    self._msg = MIMEText(fp.read(), _subtype=self.mimetype_sub)
                elif self.mimetype_main == 'image':
                    self._msg = MIMEImage(fp.read(), _subtype=self.mimetype_sub)
                elif self.mimetype_main == 'audio':
                    self._msg = MIMEAudio(fp.read(), _subtype=self.mimetype_sub)
                else:
                    self._msg = MIMEBase(self.mimetype_main, self.mimetype_sub)
                    self._msg.set_payload(fp.read())
                    # Encode the payload using Base64
                    email.encoders.encode_base64(self._msg)
                if not hasattr(self.filename, 'read'):
                    fp.close()
                self._msg.add_header('Content-Disposition', 'attachment', filename=self.name)
            return self._msg

    def add_attachment(self, filename, mimetype=None, attachment_name=None):
        self._attachments.append(Mail.Attachment(filename, mimetype, attachment_name))
        
    def remove_attachment(self, filename=None, attachment_name=None):
        if filename:
            for a in iter(self._attachments):
                if a.filename == filename:
                    del a
        elif attachment_name:
            for a in iter(self._attachments):
                if a.name == attachment_name:
                    del a

    def _prepare(self):
        if self._msg is None:
            if self._multipart:
                self._msg = MIMEMultipart()
                self._msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'
                if self._bodytext is not None:
                    self._msg.attach(MIMEText(self._bodytext))
            else:
                self._msg = MIMEText(self._bodytext if self._bodytext is not None else '')

            self._msg['Subject'] = self._subject
            self._msg['From'] = self._from
            if len(self._to) != 0:
                self._msg['To'] = Mail.COMMASPACE.join(self._to)
            if len(self._cc) != 0:
                self._msg['CC'] = Mail.COMMASPACE.join(self._cc)
            if len(self._bcc) != 0:
                self._msg['BCC'] = Mail.COMMASPACE.join(self._bcc)

            for a in self._attachments:
                self._msg.attach(a.prepare())
        return self._msg

    def __str__(self):
        self._prepare()
        return self._msg.as_string()

    @property
    def multipart(self):
        return self._multipart

    @multipart.setter
    def multipart(self, value):
        self._multipart = value
        self._msg = None

    @property
    def sender(self):
        return self._from

    @sender.setter
    def sender(self, value):
        if value is None:
            self._from = arsoft.utils.getlogin()
        else:
            self._from = value
        self._msg = None

    @property
    def recipient_to(self):
        return self._to

    @property
    def recipient_cc(self):
        return self._cc

    @property
    def recipient_bcc(self):
        return self._bcc

    @property
    def recipients(self):
        ret = []
        ret.extend(self._to)
        ret.extend(self._cc)
        ret.extend(self._bcc)
        return ret

    @property
    def subject(self):
        return self._subject
    
    @subject.setter
    def subject(self, value):
        self._subject = value
        self._msg = None

    @property
    def body(self):
        return self._bodytext
    
    @body.setter
    def body(self, value):
        self._bodytext = value
        self._msg = None

if __name__ == '__main__':
    m = Mail(to=['root'], subject='Hello')
    s = smtplib.SMTP('localhost')
    s.sendmail(m.sender, m.recipients, str(m))
    s.quit()
