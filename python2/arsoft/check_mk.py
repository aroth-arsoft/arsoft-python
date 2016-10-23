#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import errno
from arsoft.utils import runcmdAndGetData
from arsoft.timestamp import strptime_as_datetime

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

def systemd_parse_status(lines, skip_header_line=True):
    ret = {}
    got_header = False
    last_key = None
    for line in lines:
        if not got_header:
            got_header = True
        elif ':' in line:

            key, value = line.split(':', 1)
            key = key.strip().replace(' ', '_').lower()
            if key.startswith('next_') or key.startswith('last_'):
                break
            value = value.strip()
            if value == 'yes':
                value = 1
            elif value == 'no':
                value = 0
            elif len(value) > 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            if key == 'main_pid':
                (main_pid, procname) = value.split(' ', 1)
                if ' ' in main_pid:
                    pid, dummy = main_pid.split(' ', 1)
                    value = saveint(pid)
                else:
                    value = saveint(main_pid)
            elif key == 'active':
                start = value.find('(')
                if start >= 0:
                    end = value.find(')', start+1)
                    ret['state'] = value[start+1:end]
                    active = True if value[0:start].strip() == 'active' else False
                else:
                    active = False

                start = value.find('since ')
                if start >= 0:
                    end = value.find(';', start+6)
                    if end >= 0:
                        fmt = '%a %Y-%m-%d %H:%M:%S %Z'
                        ret['active_since'] = strptime_as_datetime(value[start+6:end], fmt)
                value = active
            elif key == 'condition':
                start = value.find('at ')
                if start >= 0:
                    end = value.find(';', start+3)
                    if end >= 0:
                        fmt = '%a %Y-%m-%d %H:%M:%S %Z'
                        ret['condition_since'] = strptime_as_datetime(value[start+3:end], fmt)
                    value = value[0:start].strip()
            elif key == 'loaded':
                start = value.find('(')
                if start >= 0:
                    end = value.find(')', start+1)
                    unit_file, enable_state, vendor_preset = value[start+1:end-1].split(';', 2)
                    ret['unit_file'] = unit_file
                    ret['enabled'] = True if enable_state.strip() == 'enabled' else False
                    if ':' in vendor_preset:
                        txt, st = vendor_preset.split(':', 1)
                        ret['vendor_preset_enabled'] = True if st.strip() == 'enable' else False
                    else:
                        ret['vendor_preset_enabled'] = None
                    if value[0:start-1].strip() == 'loaded':
                        value = True
                    else:
                        value = False
            ret[key] = value
            last_key = key
        elif last_key is not None:
            if last_key == 'condition':
                ret['condition_desc'] = line.strip()
            elif last_key == 'drop-in':
                if 'drop_in_depends' not in ret:
                    ret['drop_in_depends'] = []
                ret['drop_in_depends'].append(line.strip())
    return ret

def systemd_status_raw(service_name):
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(['/bin/systemctl', '--no-pager', '--lines=0', 'status', service_name], env={'LANG':'C'})
    return systemd_parse_status(lines=stdoutdata.splitlines())

def systemd_status(service_name):
    pid = 0
    running = False
    data = systemd_status_raw(service_name)
    running = True if data.get('state') == 'running' else False
    pid = data.get('main_pid')
    return (pid, running)

def timedatectl_parse_status(lines):
    ret = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().replace(' ', '_').lower()
            if key.startswith('next_') or key.startswith('last_'):
                break
            value = value.strip()
            if value == 'yes':
                value = 1
            elif value == 'no':
                value = 0
            elif len(value) > 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            if key.endswith('time'):
                if key == 'rtc_time':
                    fmt = '%a %Y-%m-%d %H:%M:%S'
                else:
                    fmt = '%a %Y-%m-%d %H:%M:%S %Z'
                value = strptime_as_datetime(value, fmt)
            ret[key] = value
    return ret

def timedatectl_status():
    pid = 0
    running = False
    data = {}
    (sts, stdoutdata, stderrdata) = runcmdAndGetData(['/usr/bin/timedatectl', '--no-pager', 'status'], env={'LANG':'C'})
    data = systemd_parse_status(lines=stdoutdata.splitlines())
    return data

def networkctl_parse_status(lines):
    ret = {}
    for line in lines:
        fields = filter(bool, line.split(' '))
        (num, lnk_name, lnk_type, lnk_op, lnk_setup) = fields
        if lnk_name != 'lo':
            iface = {'num': saveint(num), 'type':str(lnk_type), 'op': str(lnk_op), 'setup':str(lnk_setup) }
            if iface['setup'] == 'unmanaged':
                iface['managed'] = False
            else:
                iface['managed'] = True
                iface['configured'] = True if iface['setup'] == 'configured' else False
            ret[str(lnk_name)] = iface
    return ret

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

    def unknown(self, msg):
        if self.level < LEVEL_UNKNOWN:
            self.level = LEVEL_UNKNOWN
        self._list.append(msg + '(!!!)')

    def append(self, msg):
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


if __name__ == "__main__":
    print(systemd_status('systemd-timesyncd'))
    print(systemd_status('unknown-service'))
    print(systemd_status_raw('systemd-timesyncd'))
    print(timedatectl_status())
