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
        def __next__(self):
            info = next(self._list_iter)
            if info:
                return self._zipfile.open(info)
            else:
                raise StopIteration

    def __iter__(self):
        return self.ZipFileIterator(self)
    
    @staticmethod
    class default_compare_functor(object):
        def __init__(self, date_time=True, content=True):
            self.date_time = date_time
            self.content = content
        def __call__(self, selfzip, selfinfo, otherzip, otherinfo):
            ret = True
            if self.date_time and selfinfo.date_time != otherinfo.date_time:
                ret = False
            if self.content and selfinfo.CRC != otherinfo.CRC:
                print('%s changed' % (selfinfo.filename))
                ret = False
            return ret

    def compare(self, otherzip, date_time=True, content=True, compare_functor=None):
        selfinfolist = self.infolist()
        otherinfolist = otherzip.infolist()

        if compare_functor is None:
            compare_functor = ZipFileEx.default_compare_functor(date_time, content)

        ret = True if len(selfinfolist) == len(otherinfolist) else False
        if ret:
            for selfinfo in iter(selfinfolist):
                found = False
                for otherinfo in iter(otherinfolist):
                    if selfinfo.filename == otherinfo.filename:
                        found = True
                        ret = compare_functor(self, selfinfo, otherzip, otherinfo)
                        break
                if not found:
                    ret = False

                if not ret:
                    break
        return ret
