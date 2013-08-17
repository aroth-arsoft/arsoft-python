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

    def save(self, filename_or_fileobj=None, base_directory=None):
        if filename_or_fileobj is None:
            filename_or_fileobj = self._filename
        if base_directory is None:
            base_directory = self._base_directory

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
                    rel_item = os.path.relpath(it, base_directory)
                    fobj.write(rel_item + '\n')
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
        return False if self._items else True

    def __str__(self):
        return ','.join(self._items)

    def append(self, item):
        fullname = os.path.join(self._base_directory, item)
        newitems = glob.glob(fullname)
        if newitems:
            self._items = self._items.union(newitems)
        else:
            self._items.add(item)
            
    def extend(self, list):
        for item in list:
            self.append(item)

    @property
    def filename(self):
        return self._filename

    @property
    def base_directory(self):
        return self._base_directory

    @base_directory.setter
    def base_directory(self, value):
        self._base_directory = value

    def __len__(self):
        return len(self._items)

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
    def __init__(self, filename=None, base_directory=None):
        self._items = []
        self._plain_list = None
        self._base_directory = base_directory
        if filename is not None:
            self.open(filename)
            
    @staticmethod
    def from_list(list, base_directory=None):
        ret = FileList(filename=None, base_directory=base_directory)
        item = FileListItem(filename=None, base_directory=base_directory)
        item.extend(list)
        ret.append(item)
        return ret

    def clear(self):
        self._items = []
        self._plain_list = None
        self._base_directory = None

    def _build_plain_list(self):
        if self._plain_list is None:
            self._plain_list = []
            for i in self._items:
                self._plain_list.extend(i.items)

    def empty(self):
        self._build_plain_list()
        return False if self._plain_list else True

    def open(self, filename):
        self.clear()
        if isinstance(filename, list):
            for it in filename:
                self.append(it)
        else:
            self.append(filename)

    def append(self, item):
        if isinstance(item, FileListItem):
            #print('append other filelistitem with %i items' % (len(item)))
            self._items.append(item)
            if self._base_directory is None:
                self._base_directory = item.base_directory
            ret = True
        elif isinstance(item, FileList):
            #print('append other filelist with %i items' % (len(item._items)))
            for other_item in item._items:
                self._items.append(other_item)
            if self._base_directory is None:
                self._base_directory = item.base_directory
            ret = True
        else:
            if os.path.isdir(item):
                ret = True
                for f in os.listdir(item):
                    fullname = os.path.join(item, f)
                    newitem = FileListItem()
                    if not newitem.open(fullname):
                        ret = False
                    else:
                        self._items.append(newitem)
            else:
                newitem = FileListItem()
                ret = newitem.open(item)
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

    def save(self, filename_or_fileobj, base_directory=None):
        self._build_plain_list()
        newitem = FileListItem()
        newitem.items = self._plain_list
        if base_directory is None:
            newitem.base_directory = self._base_directory
        else:
            newitem.base_directory = base_directory
        return newitem.save(filename_or_fileobj)

    @property
    def items(self):
        self._build_plain_list()
        return self._plain_list

    @property
    def base_directory(self):
        return self._base_directory

    @base_directory.setter
    def base_directory(self, value):
        self._base_directory = value

    def __iter__(self):
        self._build_plain_list()
        return self._plain_list.__iter__()

    def __str__(self):
        ret = 'FileList('
        for item in self._items:
            ret += '['
            ret += str(item)
            ret += ']'
        ret += ')'
        return ret

if __name__ == "__main__":
    import sys
    fl = FileList(sys.argv[1])
    for it in fl.items:
        print(str(it))
    fl.save(sys.argv[2])
