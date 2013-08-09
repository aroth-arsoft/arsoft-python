#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import glob
import os.path

class FileListItem(object):
    def __init__(self, filename=None, base_directory=None):
        self._filename = filename
        self._base_directory = base_directory
        self._items = set()
        if filename is not None:
            self.open(filename)

    def open(self, filename_or_fileobj=None):
        if filename_or_fileobj is None:
            filename_or_fileobj = self._filename

        if isinstance(filename_or_fileobj, str):
            try:
                fobj = open(filename_or_fileobj, 'r')
            except IOError:
                fobj = None
        else:
            fobj = filename_or_fileobj

        if fobj:
            try:
                for rawline in fobj:
                    line = rawline.strip()
                    # comment or blank line?
                    if line == '':
                        # skip blank lines
                        continue
                    if line[0] == '#':
                        # skip comments
                        continue
                    self.append(line)

                fobj.close()
                ret = True
            except IOError:
                ret = False
        else:
            ret = False
        return ret

    def save(self, filename_or_fileobj=None):
        if filename_or_fileobj is None:
            filename_or_fileobj = self._filename

        if isinstance(filename_or_fileobj, str):
            try:
                fobj = open(filename_or_fileobj, 'w')
            except IOError:
                fobj = None
        else:
            fobj = filename_or_fileobj

        if fobj:
            try:
                for it in self._items:
                    fobj.write(it + '\n')
                fobj.close()
                ret = True
            except IOError:
                ret = False
        else:
            ret = False
        return ret
    def clear(self):
        self._items = set()

    def empty(self):
        return True if len(self._items) == 0 else False
    
    def __str__(self):
        return self._filename
    
    def append(self, item):
        fullname = os.path.join(self._base_directory, item)
        newitems = glob.glob(fullname)
        if newitems:
            self._items = self._items.union(newitems)
        else:
            self._items.add(item)

    @property
    def filename(self):
        return self._filename
    
    @property
    def base_directory(self):
        return self._base_directory

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        if value is None:
            self._items = []
        else:
            if isinstance(value, list):
                self._items = value
            else:
                self._items = [value]

    def __iter__(self):
        return iter(self._items)

class FileList(object):
    def __init__(self, filename=None):
        self._items = []
        self._plain_list = None
        if filename is not None:
            self.open(filename)

    def clear(self):
        self._items = []
        self._plain_list = None
        
    def _build_plain_list(self):
        if self._plain_list is None:
            self._plain_list = []
            for i in self._items:
                self._plain_list.extend(i.items)

    def empty(self):
        self._build_plain_list()
        return True if self._plain_list else False

    def open(self, filename):
        self.clear()
        if isinstance(filename, list):
            for it in filename:
                self._append(it)
        else:
            self._append(filename)

    def _append(self, filename):
        if os.path.isdir(filename):
            ret = True
            for f in os.listdir(filename):
                fullname = os.path.join(filename, f)
                newitem = FileListItem()
                if not newitem.open(fullname):
                    ret = False
                else:
                    self._items.append(newitem)
        else:
            newitem = FileListItem()
            ret = newitem.open(filename)
            if ret:
                self._items.append(newitem)
        if ret:
            self._plain_list = None
        return ret

    def save(self):
        ret = True
        for it in self._items:
            if not it.save():
                ret = False
                break
        return ret
    
    def save(self, filename_or_fileobj):
        newitem = FileListItem()
        newitem.items = self.items
        return newitem.save(filename_or_fileobj)

    @property
    def items(self):
        self._build_plain_list()
        return self._plain_list

    def __iter__(self):
        self._build_plain_list()
        return self._plain_list.__iter__()

    def __str__(self):
        ret = 'FileList('
        for item in self._items:
            ret += str(item.filename)
        ret += ')'
        return ret

if __name__ == "__main__":
    import sys
    fl = FileList(sys.argv[1])
    for it in fl.items:
        print(str(it))
    fl.save(sys.argv[2])
