#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path

class FileListItem(object):
    def __init__(self, filename=None):
        self._filename = filename
        self._items = []
        if filename is not None:
            self.open(filename)

    def open(self, filename=None):
        if filename is None:
            filename = self._filename

        try:
            f = open(filename, 'r')
            for rawline in f:
                line = rawline.strip()
                # comment or blank line?
                if line == '':
                    # skip blank lines
                    continue
                if line[0] == '#':
                    # skip comments
                    continue
                self._items.append(line)
            f.close()
            ret = True
        except IOError:
            ret = False
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self._filename

        try:
            f = open(filename, 'w')
            for it in self._items:
                f.write(it + '\n')
            f.close()
            ret = True
        except IOError:
            ret = False
        return ret
    
    @property
    def filename(self):
        return self._filename
    
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

    def __str__(self):
        return str(self._items)

class FileList(object):
    def __init__(self, filename=None):
        self._items = []
        if filename is not None:
            self.open(filename)

    def clear(self):
        self._items = []

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
            newitem = FileListItem()
            if not newitem.open(filename):
                ret = False
            else:
                self._items.append(newitem)
        return ret

    def save(self):
        ret = True
        for it in self._items:
            if not it.save():
                ret = False
        return ret
    
    def save(self, filename):
        newitem = FileListItem()
        newitem.items = self.items
        return newitem.save(filename)

    @property
    def items(self):
        ret = []
        for i in self._items:
            ret.extend(i.items)
        return ret

    def __str__(self):
        return str(self.items)

