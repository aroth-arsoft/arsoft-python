#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import errno
from arsoft.utils import runcmdAndGetData

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

def systemd_is_enabled(service_name):
    ret = False
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(['/bin/systemctl', '--no-pager', 'is-enabled', service_name])
    if sts == 0:
        ret = True if stdoutdata.find('enabled') != -1 else False
    return ret

def systemd_is_active(service_name):
    pid = 0
    running = False
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(['/bin/systemctl', '--no-pager', 'is-active', service_name], env={'LANG':'C'})
    if sts == 0:
        running = True
    return (pid, running)

def systemd_status(service_name):
    pid = 0
    running = False
    data = {}
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(['/bin/systemctl', '--no-pager', 'status', service_name], env={'LANG':'C'})
    got_header = False
    for line in stdoutdata.splitlines():
        if not line:
            got_header = True
            continue
        if got_header:
            pass
        else:
            if not ':' in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip().replace(' ', '_').lower()
            if key.startswith('next_') or key.startswith('last_'):
                break
            value = value.strip()
            if value == 'yes':
                value = 1
            elif value == 'no':
                value = 0
            data[key] = value
    running = data.get('active')
    running = True if running is not None and running.startswith('active') else False
    main_pid = data.get('main_pid')
    if main_pid:
        if ' ' in main_pid:
            pid, dummy = main_pid.split(' ', 1)
            pid = saveint(pid)
        else:
            pid = saveint(main_pid)
    return (pid, running)

def saveint(v):
    if v is None:
        return 0
    try:
        return int(v)
    except ValueError:
        return 0
