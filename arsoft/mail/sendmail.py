#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import smtplib

def sendmail(mail, server='localhost'):
    s = smtplib.SMTP(server)
    s.sendmail(mail.sender, mail.recipients, str(mail))
    s.quit()
