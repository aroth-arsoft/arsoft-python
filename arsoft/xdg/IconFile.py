#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from base import xdg_desktop_file
from arsoft.utils import runcmd

class IconFile(xdg_file):
    
    def __init__(self, filename, size, company=None, product=None, name=None, theme=None, context=None):
        super(IconFile, self).__init__(filename=filename, company=company, product=product, name=name)
        self._size = size
        self._theme = theme
        self._context = theme

    def install(self):
        args = ['install', '--size', str(self._size)]
        if self._theme is not None:
            args.extend(['--theme', self._theme])
        if self._context is not None:
            args.extend(['--context', self._context])
        args.append(self.filename)
        args.append(self.suggested_basename)

        if runcmd('xdg-icon-resource', args) == 0:
            ret = True
        else:
            ret = False
        return ret
 
