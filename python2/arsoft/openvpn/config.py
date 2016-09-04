#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import platform
import arsoft.utils

(linux_distname,linux_distversion,linux_distcodename) = platform.linux_distribution()

class OpenVPNDefaults(object):
    config_directory = '/etc/openvpn'
    if linux_distcodename == 'precise':
        run_directory = '/var/run'
    else:
        run_directory = '/run'
    config_extension = '.conf'

    has_systemd = os.path.isfile('/bin/systemctl')

    def __init__(self):
        pass

    @staticmethod
    def pidfile(vpnname):
        if linux_distcodename == 'precise':
            return os.path.join(OpenVPNDefaults.run_directory, 'openvpn.' + vpnname + '.pid')
        else:
            return os.path.join(OpenVPNDefaults.run_directory, 'openvpn', vpnname + '.pid')

class Config(object):

    def __init__(self,
                 configdir=OpenVPNDefaults.config_directory,
                 rundir=OpenVPNDefaults.run_directory,
                 extension=OpenVPNDefaults.config_extension):
        self._config_directory = configdir
        self._run_directory = rundir
        self._config_extension = extension
        self.refresh()
        self.last_error = None
        
    def refresh(self):
        self._names = {}
        if os.path.isdir(self._config_directory):
            ret = True
            for filename in os.listdir(self._config_directory):
                (basename, ext) = os.path.splitext(filename)
                if ext == self._config_extension:
                    configfilename = os.path.join(self._config_directory, filename)
                    running = self._check_running(basename)
                    self._names[basename] = { 'name': basename,
                                                'configfile': configfilename,
                                                'running': running }
        else:
            ret = False
        return ret

    def _check_running(self, vpnname):
        if os.path.isdir(self._run_directory):
            pidfile = OpenVPNDefaults.pidfile(vpnname)
            ret = arsoft.utils.isProcessRunningByPIDFile(pidfile)
        else:
            ret = False
        return ret

    def get_config_file(self, config_name):
        if config_name in self._names:
            ret = self._names[config_name]['configfile']
        else:
            ret = None
        return ret
    
    def is_running(self, config_name):
        if config_name in self._names:
            ret = self._names[config_name]['running']
        else:
            ret = None
        return ret

    def start(self, config_name):
        if config_name in self._names:
            if OpenVPNDefaults.has_systemd:
                ret = self._invoke_systemctl_openvpn('start', config_name)
            else:
                ret = self._invoke_rc_d_openvpn('start', config_name)
        else:
            ret = False
        return ret

    def stop(self, config_name):
        if config_name in self._names:
            if OpenVPNDefaults.has_systemd:
                ret = self._invoke_systemctl_openvpn('stop', config_name)
            else:
                ret = self._invoke_rc_d_openvpn('stop', config_name)
        else:
            ret = False
        return ret

    def restart(self, config_name):
        if config_name in self._names:
            if OpenVPNDefaults.has_systemd:
                ret = self._invoke_systemctl_openvpn('restart', config_name)
            else:
                ret = self._invoke_rc_d_openvpn('restart', config_name)
        else:
            ret = False
        return ret

    @property
    def names(self):
        return list(self._names.keys())

    def _invoke_rc_d_openvpn(self, action, name):
        invoke_args = ['/usr/sbin/invoke-rc.d', 'openvpn', action, name]
        (sts, stdoutdata, stderrdata) = arsoft.utils.runcmdAndGetData(invoke_args)
        if sts == 0:
            self.last_error = None
            ret = True
        else:
            self.last_error = stderrdata
            ret = False
        return ret

    def _invoke_systemctl_openvpn(self, action, name):
        invoke_args = ['/bin/systemctl', action, 'openvpn@%s.service' % name]
        (sts, stdoutdata, stderrdata) = arsoft.utils.runcmdAndGetData(invoke_args)
        if sts == 0:
            self.last_error = None
            ret = True
        else:
            self.last_error = stderrdata
            ret = False
        return ret

    def __str__(self):
        ret = "config directory: " + str(self._config_directory) + "\r\n" +\
            "config extension: " + str(self._config_extension) + "\r\n"
        if len(self._names) > 0:
            for vpn in self._names.values():
                ret = ret + '  VPN ' + vpn['name'] + ":\r\n"
                ret = ret + '    config file: ' + vpn['configfile'] + "\r\n"
                ret = ret + '    running: ' + ('yes' if vpn['running'] else 'no') + "\r\n"
        else:
            ret = ret + "No VPNs configured.\r\n"
        return ret

if __name__ == '__main__':
    c = Config()

    print(c)
