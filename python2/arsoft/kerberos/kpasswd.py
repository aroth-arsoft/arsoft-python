#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import pexpect
import sys

def kpasswd(principal, oldpassword, newpassword, verbose=False):
    child = pexpect.spawn('/usr/bin/kpasswd', [principal], env={'LANG':'C'})
    if verbose:
        child.logfile = sys.stdout
    if child:
        if child.expect(['[Pp]assword:', pexpect.EOF]) == 0:
            child.sendline(oldpassword)
            if child.expect(['New password', pexpect.EOF]) == 0 and \
                child.expect([':', pexpect.EOF]) == 0:
                child.sendline(newpassword)
                if child.expect(['Verify password - New password', pexpect.EOF]) == 0 and \
                    child.expect([':', pexpect.EOF]) == 0:
                    child.sendline(newpassword)
                    child.wait()
                    last_message = child.read().strip()
                    child.close()
                    ret = True if child.exitstatus == 0 else False
                    if ret:
                        (status, message) = last_message.split(':')
                        status = status.strip()
                        if status == 'Success':
                            ret = True
                            error_message = None
                        else:
                            ret = False
                            error_message = message.strip()
                else:
                    child.close()
                    ret = False
                    error_message = 'New password was not accepted.'
            else:
                child.close()
                ret = False
                error_message = 'Old password was not accepted.'
        else:
            child.close()
            ret = False
            error_message = 'Unexpected output from kpasswd.'
    else:
        ret = False
        error_message = 'Failed to start kpasswd tool.'
    return (ret, error_message)

if __name__ == '__main__':
    (ret, error_message) = kpasswd('tux', 'tuxer0', 'tuxedo', verbose=True)
    print(ret, error_message)
    (ret, error_message) = kpasswd('tux', 'tuxedo', 'tuxer0', verbose=True)
    print(ret, error_message)
    (ret, error_message) = kpasswd('tux', 'tuxedo', 'tuxer0', verbose=True)
    print(ret, error_message)
