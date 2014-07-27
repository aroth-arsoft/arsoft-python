#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import subprocess
import arsoft.utils

class export(object):
    def __init__(self, dir, client, options):
        self._dir = dir
        self._client = client
        self._options = options

    @property
    def directory(self):
        return self._dir

    @property
    def client(self):
        return self._client

    @property
    def options(self):
        return self._options
    
    def __str__(self):
        return self._dir + '\t' + self._client + '(' + ','.join(self._options) + ')'

    @staticmethod
    def fromETabLine(line):
        dir = None
        client = None
        options = None
        idx = line.find('\t')
        if idx > 0:
            dir = line[0:idx]
            line = line[idx+1:]
            idx = line.find('(')
            endidx = line.find(')')
            if idx > 0 and endidx > idx:
                client = line[0:idx]
                options = line[idx+1:endidx].split(',')
        if dir is not None and client is not None and options is not None:
            return export(dir, client, options)
        else:
            return None
    
class exports(object):
    def __init__(self):
        self._entries = None
        self._last_error = None

    def _dirty(self):
        self._entries = None

    def _refresh(self):
        self._entries = []
        try:
            fetab = open('/var/lib/nfs/etab', 'r')
            for line in fetab:
                entry = export.fromETabLine(line)
                if entry is not None:
                    self._entries.append(entry)
                else:
                    self._last_error = 'etab parser error: invalid line: ' + line
            fetab.close()
            ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False
        return ret
    
    def get_directory(self, directory):
        ret = []
        for entry in self._entries:
            if entry.directory == directory:
                ret.append(entry)
        return ret

    def export(self, directory, clients=None):
        ret = exports._export(directory, clients)
        if ret:
            self._dirty()
        return ret
    
    def unexport(self, directory, clients=None):
        ret = True
        if clients is None:
            for entry in self._entries:
                if entry.directory == directory:
                    if not exports._unexport(entry.directory, entry.client):
                        ret = False
                    else:
                        self._dirty()
        else:
            ret = exports._unexport(directory, clients)
            if ret:
                self._dirty()
        return ret

    def reexport(self):
        (exitcode, output, error) = exports._exportfs(['-r'])
        return True if exitcode == 0 and len(error) == 0 else False

    def __str__(self):
        ret = ''
        for entry in self._entries:
            ret = ret + str(entry) + "\n"
        return ret

    @property
    def entries(self):
        if self._entries is None:
            self._refresh()
        return self._entries

    @property
    def last_error(self):
        return self._last_error

    @staticmethod
    def _export(directory, clients=None, options=[]):
        args = []
        if len(options) > 0:
            args.append('-o')
            args.append(','.join(options))
        if clients is None:
            args.append('*:' + directory)
        else:
            for client in clients:
                args.append(client + ':' + directory)
        (exitcode, output, error) = exports._exportfs(args)
        return True if exitcode == 0 and len(error) == 0 else False

    @staticmethod
    def _unexport(directory, clients=None):
        args = ['-u']
        if clients is None:
            args.append('*:' + directory)
        else:
            for client in clients:
                args.append(client + ':' + directory)
        (exitcode, output, error) = exports._exportfs(args)
        return True if exitcode == 0 and len(error) == 0 else False

    @staticmethod
    def _exportfs(args):
        return arsoft.utils.runcmdAndGetData('/usr/sbin/exportfs', args)

if __name__ == '__main__':
    
    mgr = exports()
    for e in mgr.entries:
        print (e)
    
    if not mgr.unexport('/export'):
        print('unexport failed')

    for e in mgr.entries:
        print (e)
