#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from base import xdg_desktop_file, xdg_menu_file
from arsoft.utils import runcmd
import os.path
import tempfile
from xml.dom.minidom import parse, getDOMImplementation

class DesktopMenuItem(xdg_desktop_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(DesktopMenuItem, self).__init__(filename=filename, company=company, product=product, name=name, ext='.desktop', maingroup='Desktop Entry')
        if filename is None:
            self.Version = '1.0'
            self.Encoding = 'UTF-8'

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

class DesktopDirectory(xdg_desktop_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(DesktopMenuItem, self).__init__(filename=filename, company=company, product=product, name=name, ext='.directory', maingroup='Desktop Entry')
        if filename is None:
            self.Version = '1.0'
            self.Encoding = 'UTF-8'

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
    de = DesktopMenuItem(company='arsoft', product='test', name='editor')
    print de.company
    print de.product
    print de.name
    de.Version = '1.0'
    de.Categories = ['Utility', 'KDE']
    de.Keywords = ['Bar', 'Foo']
    de.save('test.desktop')
    de.install()
    
    de2 = DesktopMenuItem('test.desktop')
    print de2.Version
    print de2.Categories
    print de2.Keywords
    
    m1 = DesktopMenu('/etc/xdg/menus/kde4-applications.menu')
    print(m1.root)
    
    m2 = DesktopMenu()
    m2.root.name = 'Applications'
    m2.root.add_child('Tools', 'dirddname')
    m2.root.add_child('Tools', 'dirname', includes=['test.desktop'])
    print(m2.root)
    m2.save('test.menu')
