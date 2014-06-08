#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from base import xdg_desktop_file
from arsoft.utils import runcmd
import os.path
import tempfile

class DesktopMenuItem(xdg_desktop_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(DesktopMenuItem, self).__init__(filename=filename, company=company, product=product, name=name, ext='.desktop', maingroup='Desktop Entry')
        if filename is None:
            self.Version = '1.0'
            self.Encoding = 'UTF-8'

    def install(self, verbose=False):
        tmppath = tempfile.mkdtemp()
        tmpfile = os.path.join(tmppath, self.suggested_basename)
        ret = self.save(tmpfile)
        if ret:
            args = ['install', tmpfile]
            if runcmd('xdg-desktop-menu', args, verbose=verbose) == 0:
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
