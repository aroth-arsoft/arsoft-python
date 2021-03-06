#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import pexpect
import sys
import os.path

class _kpasswd_output(object):
    def __init__(self, executable, verbose=False):
        self.executable_names = [ executable, os.path.basename(executable) ]
        self._verbose = False
        self._messages = []
    def write(self, s):
        if self._verbose:
            print(s)
        self._messages.append(s.decode('utf8').strip())
    def flush(self):
        pass

    @property
    def message(self):
        return '\n'.join(self._messages)

    @property
    def last_message(self):
        ret = None
        if self._messages:
            ret = self._messages[-1]
            if ':' in ret:
                (prefix, msg) = ret.split(':', 1)
                if prefix in self.executable_names:
                    ret = msg.strip()
        return ret

def kpasswd(principal, oldpassword, newpassword, verbose=False, timeout=5, executable='/usr/bin/kpasswd'):
    ret = False
    error_message = None
    child = pexpect.spawn(executable, [principal], env={'LANG':'C'}, timeout=5)
    child.logfile = _kpasswd_output(executable, verbose=verbose)
    if child:
        if child.expect(['[Pp]assword.*:', pexpect.EOF]) == 0:
            child.sendline(oldpassword)
            if child.expect(['(New password|Enter new password)', pexpect.EOF]) == 0 and \
                child.expect([':', pexpect.EOF]) == 0:
                child.sendline(newpassword)
                if child.expect(['(Verify password - New password|Enter it again)', pexpect.EOF]) == 0 and \
                    child.expect([':', pexpect.EOF]) == 0:
                    child.sendline(newpassword)
                    child.wait()
                    last_message = child.read().strip().decode('utf8')
                    error_message = last_message
                    child.close()
                    ret = True if child.exitstatus == 0 else False
                    if ret:
                        if ':' in last_message:
                            (status, message) = last_message.split(':', 1)
                            status = status.strip()
                            error_message = message.strip()
                            ret = True if status == 'Success' else False
                        elif 'Password changed':
                            ret = True
                    else:
                        pass
                else:
                    error_message = 'New password was not accepted: %s' % child.logfile.last_message
                    child.close()
            else:
                #error_message = 'Old password was not accepted: %s' % child.logfile.last_message
                error_message = 'Old password was not accepted: %s' % child.logfile.last_message
                child.close()
        else:
            error_message = child.logfile.last_message
            child.close()
    else:
        error_message = 'Failed to start kpasswd tool.'
    return (ret, error_message)

if __name__ == '__main__':
    if len(sys.argv) == 4:
        (ret, error_message) = kpasswd(sys.argv[1], sys.argv[2], sys.argv[3], verbose=True)
        print(ret, error_message)
    else:
        (ret, error_message) = kpasswd('tux', 'tuxer0', 'tuxedo', verbose=True)
        print(ret, error_message)
        (ret, error_message) = kpasswd('tux', 'tuxedo', 'tuxer0', verbose=True)
        print(ret, error_message)
        (ret, error_message) = kpasswd('tux', 'tuxedo', 'tuxer0', verbose=True)
        print(ret, error_message)
