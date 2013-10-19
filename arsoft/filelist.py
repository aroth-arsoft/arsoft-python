#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import glob
import os.path

class FileListItemBase(object):
    def __init__(self, filename=None, base_directory=None, use_glob=True):
        self._filename = filename
        self._base_directory = base_directory
        self._use_glob = use_glob
        self._items = None
        self.clear()
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
                for it in self.__iter__():
                    it_str = self._item_to_string(it)
                    fobj.write(it_str + '\n')
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

    def _item_to_string(self, item):
        if self._base_directory:
            return os.path.relpath(item, self._base_directory)
        else:
            return item

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

    def extend(self, list):
        for item in list:
            self.append(item)

class FileListItem(FileListItemBase):
    def __init__(self, filename=None, base_directory=None, use_glob=True):
        FileListItemBase.__init__(self, filename, base_directory, use_glob)

    def append(self, item):
        fullname = os.path.join(self._base_directory, item)
        if self._use_glob:
            newitems = glob.glob(fullname)
            if newitems:
                self._items = self._items.union(newitems)
            else:
                self._items.add(item)
        else:
            self._items.add(item)

    def __iter__(self):
        return iter(self._items)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        self.clear()
        if isinstance(value, list):
            for i in value:
                self.append(i)
        else:
            self.append(value)
    

class FileListItemWithDestination(FileListItemBase):
    def __init__(self, filename=None, base_directory=None, dest_base_directory=None, use_glob=True):
        FileListItemBase.__init__(self, filename, base_directory, use_glob)
        self._dest_base_directory = dest_base_directory

    @property
    def dest_base_directory(self):
        return self._dest_base_directory

    @dest_base_directory.setter
    def dest_base_directory(self, value):
        self._dest_base_directory = value

    def clear(self):
        self._items = {}

    def __iter__(self):
        return self._items.iteritems()

    def _item_to_string(self, item):
        (source, dest) = item
        if self._base_directory is not None:
            source_full = os.path.relpath(source, self._base_directory)
        else:
            source_full = source
        if self._dest_base_directory is not None:
            dest_full = os.path.relpath(dest, self._dest_base_directory)
        else:
            dest_full = dest

        #print('_item_to_string %s=%s' % (source_full, dest_full))
        return '%s=%s' % (source_full, dest_full)

    def append(self, item):
        if '=' in item:
            (source, dest) = item.split('=', 1)
        else:
            source = item
            dest = None
        self._append(source, dest)

    def _append(self, source, dest):
        source_fullname = os.path.join(self._base_directory, source)
        if self._use_glob:
            newitems = glob.glob(source_fullname)
            if newitems:
                for newitem in newitems:
                    if newitem == source_fullname: continue
                    if dest is None:
                        dest_fullname = os.path.basename(newitem)
                    else:
                        if self._dest_base_directory:
                            dest_fullname = os.path.join(self._dest_base_directory, dest)
                        else:
                            dest_fullname = dest
                    self._items[newitem] = dest_fullname
            else:
                if dest is None:
                    dest_fullname = os.path.basename(newitem)
                else:
                    if self._dest_base_directory:
                        dest_fullname = os.path.join(self._dest_base_directory, dest)
                    else:
                        dest_fullname = dest
                self._items[source] = dest_fullname
        else:
            if dest is None:
                dest_fullname = os.path.basename(newitem)
            else:
                if self._dest_base_directory:
                    dest_fullname = os.path.join(self._dest_base_directory, dest)
                else:
                    dest_fullname = dest
            self._items[source] = dest_fullname


    @property
    def items(self):
        #print('return items %s' % self._items)
        return self._items

    @items.setter
    def items(self, value):
        self.clear()
        if isinstance(value, dict):
            for (source, dest) in value.iteritems():
                self._append(source, dest)
        else:
            self.append(value)

class FileListBase(object):
    def __init__(self, filename=None, base_directory=None, use_glob=True):
        self._items = []
        self._plain_list = None
        self._base_directory = base_directory
        self._use_glob = use_glob
        if filename is not None:
            self.open(filename)

    def clear(self):
        self._items = []
        self._plain_list = None
        self._base_directory = None

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

    def save(self):
        ret = True
        for it in self._items:
            if not it.save():
                ret = False
                break
        return ret

    def save(self, filename_or_fileobj, base_directory=None):
        self._build_plain_list()
        if self._items:
            newitem = self._items[0].__class__()
            newitem.items = self._plain_list
            if base_directory is None:
                newitem.base_directory = self._base_directory
            else:
                newitem.base_directory = base_directory
        else:
            # just use an empty FileListItem to create a empty file
            newitem = FileListItem()
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

    def __str__(self):
        ret = '%s(' % self.__class__.__name__
        for item in self.__iter__():
            ret += '['
            ret += str(item)
            ret += ']'
        ret += ')'
        return ret

class FileList(FileListBase):
    def __init__(self, filename=None, base_directory=None, use_glob=True):
        FileListBase.__init__(self, filename, base_directory, use_glob)

    @staticmethod
    def from_list(list, base_directory=None, use_glob=True):
        ret = FileList(filename=None, base_directory=base_directory, use_glob=use_glob)
        item = FileListItem(filename=None, base_directory=base_directory, use_glob=use_glob)
        item.extend(list)
        ret.append(item)
        return ret

    def _build_plain_list(self):
        if self._plain_list is None:
            self._plain_list = []
            for i in self._items:
                self._plain_list.extend(i.items)

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

    def __iter__(self):
        self._build_plain_list()
        return self._plain_list.__iter__()

class FileListWithDestination(FileListBase):
    def __init__(self, filename=None, base_directory=None, dest_base_directory=None, use_glob=True):
        FileListBase.__init__(self, filename, base_directory, use_glob)
        self._dest_base_directory = dest_base_directory

    @property
    def dest_base_directory(self):
        return self._dest_base_directory

    @dest_base_directory.setter
    def dest_base_directory(self, value):
        self._dest_base_directory = value

    @staticmethod
    def from_list(list, base_directory=None, dest_base_directory=None, use_glob=True):
        ret = FileListWithDestination(filename=None, base_directory=base_directory, dest_base_directory=dest_base_directory, use_glob=use_glob)
        item = FileListItemWithDestination(filename=None, base_directory=base_directory, dest_base_directory=dest_base_directory, use_glob=use_glob)
        item.extend(list)
        ret.append(item)
        return ret

    def _build_plain_list(self):
        if self._plain_list is None:
            self._plain_list = {}
            for i in self._items:
                for it in i.__iter__():
                    (source, dest) = it
                    self._plain_list[source] = dest

    def append(self, item):
        if isinstance(item, FileListItemWithDestination):
            self._items.append(item)
            if self._base_directory is None:
                self._base_directory = item.base_directory
            ret = True
        elif isinstance(item, FileListWithDestination):
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
                    newitem = FileListItemWithDestination()
                    if not newitem.open(fullname):
                        ret = False
                    else:
                        self._items.append(newitem)
            else:
                newitem = FileListItemWithDestination()
                ret = newitem.open(item)
                if ret:
                    self._items.append(newitem)
        if ret:
            self._plain_list = None
        return ret

    def __iter__(self):
        self._build_plain_list()
        return self._plain_list.iteritems()

if __name__ == "__main__":
    import sys
    #fl = FileList(sys.argv[1])
    #for it in fl.items:
        #print(str(it))
    #fl.save(sys.argv[2])
    fl = FileListWithDestination(sys.argv[1])
    print(fl)
    for it in fl.items.iteritems():
        print('got fl.item %s' % str(it))
    for it in fl:
        print('got item %s' % str(it))
    fl.save(sys.argv[2])
