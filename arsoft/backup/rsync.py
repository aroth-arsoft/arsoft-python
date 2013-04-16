#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from FileList import *
from arsoft.utils import runcmd

class rsync:
    
    DEFAULT_RSYNC_BIN = '/usr/bin/rsync'
    
    def __init__(self, source, dest, include=None, exclude=None, recursive=True, preservePermissions=True, verbose=False, rsync_bin=rsync.DEFAULT_RSYNC_BIN):
        self._rsync_bin = rsync_bin
        self._source = source
        self._dest = dest
        self.verbose = verbose
        self.recursive = recursive
        self.preservePermissions = preservePermissions
        self._include = include
        self._exclude = exclude
    """
                           repeated: --filter='- .rsync-filter'
     --exclude=PATTERN       exclude files matching PATTERN
     --exclude-from=FILE     read exclude patterns from FILE
     --include=PATTERN       don't exclude files matching PATTERN
     --include-from=FILE     read include patterns from FILE
     --files-from=FILE       read list of source-file names from FILE
     """
     
    def execute(self):
        args = []
        if self.verbose:
            args.extend('-v')
        if self.recursive:
            args.extend('-r')
        if self.preservePermissions:
            args.extend('-p')
        args.extend(source)
        args.extend(dest)
        runcmd(self._rsync_bin, args)

if __name__ == "__main__":
    pass 
