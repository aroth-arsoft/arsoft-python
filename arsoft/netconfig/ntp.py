#!/usr/bin/python

from main import *

class NTPConfig(object):
    m_filename = '/etc/ntp.conf'
    m_content = []
    m_cfg = {}
    m_netconfig = None
    m_regex = None
    m_linemap = {}
    m_environ = {'confdir':'/etc',
                    'varlib':'/var/lib/ntp'
                }
    def __init__(self, netconfig=None):
        if netconfig != None:
            self.m_netconfig = netconfig
        else:
            self.m_netconfig = Netconfig()
        self.m_netconfig.addEnvironment(self.m_environ)
        self.m_cfg = IniFile(self.m_filename)
        #print self.m_cfg

    def set(self, key, value):
        self.m_cfg.set('default', key, value)

    def apply(self):
        self.set('server', self.m_netconfig.getStringList('ntp/server'))
        self.set('restrict', self.m_netconfig.getStringList('ntp/restrict'))
        self.set('broadcast', self.m_netconfig.getStringList('ntp/broadcast'))
        #print self.m_cfg
        self.m_cfg.save(self.m_filename)
