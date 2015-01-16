#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .base import xdg_desktop_file
from arsoft.utils import runcmd
import os.path
import tempfile

class DesktopDirectory(xdg_desktop_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(DesktopDirectory, self).__init__(filename=filename, company=company, product=product, name=name, ext='.directory', maingroup='Desktop Entry')
        if filename is None:
            self.Version = '1.0'
            self.Encoding = 'UTF-8'

    def install(self, verbose=False):
        tmppath = tempfile.mkdtemp()
        tmpfile = os.path.join(tmppath, self.suggested_basename)
        ret = self.save(tmpfile)
        if ret:
            args = ['xdg-desktop-menu', 'install', tmpfile]
            if runcmd(args, verbose=verbose) == 0:
                ret = True
            else:
                ret = False
        os.remove(tmpfile)
        os.rmdir(tmppath)
        return ret
 
