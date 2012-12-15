#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import arsoft.utils

class Config(object):

    def __init__(self, configdir='/etc/openvpn', rundir='/run', extension='.conf'):
        self._config_directory = configdir
        self._run_directory = rundir
        self._config_extension = extension
        self._refresh()
        
    def _refresh(self):
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
            pidfile = os.path.join(self._run_directory, 'openvpn.' + vpnname + '.pid')
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
