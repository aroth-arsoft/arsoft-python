#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from base import xdg_menu_file
from arsoft.utils import runcmd
import os.path
import tempfile

class DesktopMenu(xdg_menu_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        print('DesktopMenu')
        super(DesktopMenu, self).__init__(filename, company, product, name)

    def install(self):
        tmppath = tempfile.mkdtemp()
        tmpfile = os.path.join(tmppath, self.suggested_basename)
        ret = self.save(tmpfile)
        if ret:
            args = ['install', tmpfile]
            if runcmd('xdg-desktop-menu', args) == 0:
                ret = True
            else:
                ret = False
        os.remove(tmpfile)
        os.rmdir(tmppath)
        return ret

if __name__ == '__main__':
    m1 = DesktopMenu('/etc/xdg/menus/kde4-applications.menu')
    print(m1.root)
    
    m2 = DesktopMenu()
    m2.root.name = 'Applications'
    m2.root.add_child('Tools', 'dirddname')
    m2.root.add_child('Tools', 'dirname', includes=['test.desktop'])
    print(m2.root)
    m2.save('test.menu')
 
