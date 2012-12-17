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
        self._entries = []
        self._refresh()
        
    def _refresh(self):
        self._entries = []
        try:
            fetab = open('/var/lib/nfs/etab', 'r')
            for line in fetab:
                entry = export.fromETabLine(line)
                if entry is not None:
                    self._entries.append(entry)
                else:
                    print('invalid line: ' + line)
            fetab.close()
            ret = True
        except IOError:
            ret = False
        return ret
    
    def get_directory(self, directory):
        ret = []
        for entry in self._entries:
            if entry.directory == directory:
                ret.append(entry)
        return ret
    
    def unexport(self, directory, client=None):
        ret = True
        if client is None:
            for entry in self._entries:
                if entry.directory == directory:
                    if not exports._unexport(entry.client, entry.directory):
                        ret = False
        else:
            ret = exports._unexport(client, directory)
        return ret

    def reexport(self):
        (exitcode, output, error) = exports._exportfs(['-r'])
        return True if exitcode == 0 and len(error) == 0 else False

    def __str__(self):
        ret = ''
        for entry in self._entries:
            ret = ret + str(entry) + "\n"
        return ret

    @staticmethod
    def _export(client, directory, options=[]):
        args = []
        if len(options) > 0:
            args.append('-o')
            args.append(','.join(options))
        args.append(client + ':' + directory)
        (exitcode, output, error) = exports._exportfs(args)
        return True if exitcode == 0 and len(error) == 0 else False

    @staticmethod
    def _unexport(client, directory):
        (exitcode, output, error) = exports._exportfs(['-u', client + ':' + directory])
        return True if exitcode == 0 and len(error) == 0 else False

    @staticmethod
    def _exportfs(args):
        return arsoft.utils.runcmdAndGetData('/usr/sbin/exportfs', args)

if __name__ == '__main__':
    
    e = exports()
    print (e)
    
    if not e.unexport('/export'):
        print('unexport failed')
