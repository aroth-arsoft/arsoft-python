#!/usr/bin/python

import os

class Service(object):
    m_init_script_path = '/etc/init.d'
    m_runlevel_path = '/etc/rc%i.d'
    m_init_script = ''
    m_name = ''
    def __init__(self, name):
        self.m_filename = self.m_init_script_name + '/' + name
        self.m_name = name
        
    def reload(self):
        os.system(self.m_filename + ' reload')
        
    def start(self):
        os.system(self.m_filename + ' start')
        
    def stop(self):
        os.system(self.m_filename + ' stop')
        
    def restart(self):
        os.system(self.m_filename + ' restart')
        
    def isRunning(self):
        os.system(self.m_filename + ' status')
        return False

    def enable(self, runlevel, number):
        rcfile= self.m_runlevel_path%runlevel + 'S%02i%s'%(number, self.m_name)
        os.symlink(self.m_init_script_name + '/' + self.m_name, rcfile)
        
    def disable(self, runlevel):
        rcfile= self.m_runlevel_path%runlevel + 'S%02i%s'%(number, self.m_name)
        os.unlink(rcfile)
