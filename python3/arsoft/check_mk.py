#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import errno

def check_pid(pid):
    """ Check For the existence of a unix pid. """
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True

def check_running(pidfile):
    pid = 0
    running = False
    if os.path.isfile(pidfile):
        content = None
        try:
            with open(pidfile) as f:
                content = f.readlines()
        except IOError:
            pass
        try:
            if content:
                pid = saveint(content[0].strip())
        except ValueError:
            pass
        running = check_pid(pid)
    return (pid, running)

def saveint(v):
    if v is None:
        return 0
    try:
        return int(v)
    except ValueError:
        return 0
