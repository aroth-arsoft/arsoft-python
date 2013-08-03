#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import smtplib

def sendmail(mail, server='localhost', port=25, lmtp=False, ssl=False, starttls=False, debuglevel=0):
    if lmtp:
        s = smtplib.LMTP(server, port)
    elif ssl:
        s = smtplib.SMTP_SSL(server, port)
    else:
        s = smtplib.SMTP(server, port)
        if starttls:
            s.starttls()
    s.set_debuglevel(debuglevel)
    s.sendmail(mail.sender, mail.recipients, str(mail))
    s.quit()
