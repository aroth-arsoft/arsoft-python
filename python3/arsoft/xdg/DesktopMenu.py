#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .base import xdg_menu_file
from arsoft.utils import runcmd
import os.path
import tempfile
from os.path import expanduser
home = expanduser("~")

class DesktopMenu(xdg_menu_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(DesktopMenu, self).__init__(filename, company, product, name)

    def install(self, user=True):
        if user:
            menudir = os.path.expanduser('~/.config/menus/applications-merged')
        else:
            menudir = os.path.expanduser('/etc/xdg/menus/applications-merged')
            
        menu_filename = os.path.join(menudir, self.suggested_basename)
        ret = self.save(menu_filename)
        return ret

if __name__ == '__main__':
    m1 = DesktopMenu('/etc/xdg/menus/kde4-applications.menu')
    print(m1.root)
    
    m2 = DesktopMenu(company='arsoft', product='hello', name='world')
    m2.root.name = 'Applications'
    m2.root.add_child('Tools', 'dirddname')
    m2.root.add_child('Tools', 'dirname', includes=['test.desktop'])
    print(m2.root)
    m2.save('test.menu')

    m2.install()
 
