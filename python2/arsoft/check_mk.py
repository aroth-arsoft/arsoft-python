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

def has_systemd():
    return os.path.isfile('/bin/systemctl')

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

# taken from file:///opt/puppetlabs/puppet/lib/ruby/vendor_ruby/puppet/provider/service/debian.rb
def _debian_start_link_count(service_name):
    import glob
    return len(glob.glob('/etc/rc*.d/S??' + service_name))

# taken from file:///opt/puppetlabs/puppet/lib/ruby/vendor_ruby/puppet/provider/service/debian.rb
def is_debian_service_enabled(service_name):
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(["/usr/sbin/invoke-rc.d", "--quiet", "--query", service_name, "start"])
    # 104 is the exit status when you query start an enabled service.
    # 106 is the exit status when the policy layer supplies a fallback action
    # See x-man-page://invoke-rc.d
    if sts in [104, 106]:
        return True
    elif sts in [101, 105]:
        # 101 is action not allowed, which means we have to do the check manually.
        # 105 is unknown, which generally means the iniscript does not support query
        # The debian policy states that the initscript should support methods of query
        # For those that do not, peform the checks manually
        # http://www.debian.org/doc/debian-policy/ch-opersys.html
        return True if _debian_start_link_count(service_name) >= 4 else False
    else:
        return False

def saveint(v):
    if v is None:
        return 0
    try:
        return int(v)
    except ValueError:
        return 0

LEVEL_OK = 0
LEVEL_WARN = 1
LEVEL_CRIT = 2
LEVEL_UNKNOWN = 3

class check_state(object):
    def __init__(self):
        self._list = []
        self.perfdata = []
        self.level = LEVEL_OK

    def warning(self, msg):
        if self.level < LEVEL_WARN:
            self.level = LEVEL_WARN
        self._list.append(msg + '(!)')

    def critical(self, msg):
        if self.level < LEVEL_CRIT:
            self.level = LEVEL_CRIT
        self._list.append(msg + '(!!)')

    def ok(self, msg):
        if self.level == LEVEL_OK:
            self._list.append(msg)

    def __str__(self):
        return self.message

    @property
    def is_ok(self):
        return True if self.level == LEVEL_OK else False

    @property
    def is_warning(self):
        return True if self.level == LEVEL_WARN else False

    @property
    def is_critical(self):
        return True if self.level == LEVEL_CRIT else False

    @property
    def is_unknown(self):
        return True if self.level == LEVEL_UNKNOWN else False

    @property
    def messages(self):
        return self._list

    @property
    def message(self):
        if self._list:
            str_details = ','.join(self._list)
        else:
            str_details = ''

        # Construct a the status message.
        if self.level == LEVEL_OK:
            return "OK - " + str_details
        elif self.level == LEVEL_WARN:
            return "WARN - " + str_details
        elif self.level == LEVEL_CRIT:
            return "CRIT - " + str_details
        elif self.level == LEVEL_UNKNOWN:
            return "UNKOWN - " + str_details
        else:
            return "UNKOWN(%i) - " % self.level + str_details

    @property
    def return_value(self):
        return (self.level, self.message, self.perfdata)
