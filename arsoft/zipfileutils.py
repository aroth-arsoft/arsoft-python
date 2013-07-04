#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import zipfile

class ZipFileEx(zipfile.ZipFile):
    
    class ZipFileIterator(object):
        def __init__(self, zipfile):
            self._zipfile = zipfile
            self._list = zipfile.infolist()
            self._list_iter = iter(self._list)
        def __iter__(self):
            return self
        def next(self):
            info = next(self._list_iter)
            if info:
                return self._zipfile.open(info)
            else:
                raise StopIteration

    def __iter__(self):
        return self.ZipFileIterator(self)
