#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import tempfile
from FileList import *
from arsoft.utils import runcmdAndGetData
import urlparse
import subprocess
import sys

(python_major, python_minor, python_micro, python_releaselevel, python_serial) = sys.version_info

class RsyncDefaults(object):
    RSYNC_BIN = '/usr/bin/rsync'

class Rsync(object):
    def __init__(self, source, dest, include=None, exclude=None, 
                 recursive=True, 
                 preservePermissions=True, preserveOwner=True, preserveGroup=True, preserveTimes=True, 
                 preserveDevices=True, preserveSpecials=True, perserveACL=False, preserveXAttrs=False,
                 verbose=False, compress=True, links=True, dryrun=False,
                 delete=False, deleteExcluded=False, force=False, delayUpdates=False,
                 rsh=None, bandwidthLimit=None,
                 use_ssh=False, ssh_key=None,
                 rsync_bin=RsyncDefaults.RSYNC_BIN):
        self._rsync_bin = rsync_bin
        self._source = source
        self._dest = dest
        self.verbose = verbose
        self.recursive = recursive
        self.links = links
        self.compress = compress
        self.preservePermissions = preservePermissions
        self.preserveOwner = preserveOwner
        self.preserveGroup = preserveGroup
        self.preserveTimes = preserveTimes
        self.preserveDevices = preserveDevices
        self.preserveSpecials = preserveSpecials
        self.perserveACL = perserveACL
        self.preserveXAttrs = preserveXAttrs
        self.delete = delete
        self.deleteExcluded = deleteExcluded
        self.force = force
        self.delayUpdates = delayUpdates
        self.dryrun = dryrun
        self.rsh = rsh
        self.use_ssh = use_ssh
        self.ssh_key = ssh_key
        self.bandwidthLimit = bandwidthLimit
        self._include = include
        self._exclude = exclude

    def execute(self):
        if self._source is None or \
            (isinstance(self._source, str) and len(self._source) == 0) or \
            (isinstance(self._source, FileList) and self._source.empty()):
            raise ValueError('invalid source file or directory %s'%(str(self._source)))

        if self._dest is None or \
            (isinstance(self._dest, str) and len(self._dest) == 0) or \
            (isinstance(self._dest, FileList) and self._dest.empty()):
            raise ValueError('invalid destination file or directory %s'%(str(self._dest)))

        if self._rsync_bin is None or len(self._rsync_bin) == 0:
            raise ValueError('Invalid rsync executeable %s specified'%(str(self._rsync_bin)))

        args = []
        if self.verbose:
            args.append('--verbose')
        if self.recursive:
            args.append('--recursive')
        if self.links:
            args.append('--links')
        if self.preservePermissions:
            args.append('--perms')
        if self.preserveOwner:
            args.append('--owner')
        if self.preserveGroup:
            args.append('--group')
        if self.preserveTimes:
            args.append('--times')
        if self.preserveDevices:
            args.append('--devices')
        if self.preserveSpecials:
            args.append('--specials')
        if self.perserveACL:
            args.append('--acls')
        if self.preserveXAttrs:
            args.append('--xattrs')
        if self.compress:
            args.append('--compress')
        if self.delete:
            args.append('--delete')
        if self.deleteExcluded:
            args.append('-delete-excluded')
        if self.force:
            args.append('--force')
        if self.delayUpdates:
            args.append('--delay-updates')
        if self.dryrun:
            args.append('--dry-run')
        if self.rsh:
            args.append('--rsh=' + str(self.rsh))
        elif self.use_ssh:
            # use ssh with disable X11 forwarding
            rsh = '/usr/bin/ssh -x'
            if self.ssh_key:
                rsh = rsh + ' -i ' + self.ssh_key
            args.append('--rsh=' + str(rsh))
        if self.bandwidthLimit:
            args.append('--bwlimit=' + str(self.bandwidthLimit))

        tmp_include = None
        tmp_exclude = None
        tmp_source = None
        if self._include:
            tmp_fd, tmp_include = tempfile.mkstemp()
            tmp_fobj = os.fdopen(tmp_fd, 'w')
            if not self._include.save(tmp_fobj):
                raise IOError
            tmp_fobj.close()
            args.append('--include-from=' + tmp_include)
            if self.verbose:
                print(self._include)

        if self._exclude:
            tmp_fd, tmp_exclude = tempfile.mkstemp()
            tmp_fobj = os.fdopen(tmp_fd, 'w')
            if not self._exclude.save(tmp_fobj):
                raise IOError
            tmp_fobj.close()
            args.append('--exclude-from=' + tmp_exclude)
            if self.verbose:
                print(self._exclude)

        if isinstance(self._source, FileList):
            tmp_fd, tmp_source = tempfile.mkstemp()
            tmp_fobj = os.fdopen(tmp_fd, 'w')
            if not self._source.save(tmp_fobj):
                raise IOError
            tmp_fobj.close()
            args.append('--files-from=' + tmp_source)
            if self._source.base_directory:
                args.append(self._source.base_directory)
            else:
                args.append('/')
            if self.verbose:
                print(self._source)
        else:
            args.append(self._source)
        args.append(self._normalize_url(self._dest))

        if self.verbose:
            print("runcmd " + ' '.join(args))

        (status_code, stdout, stderr) = runcmdAndGetData(self._rsync_bin, args)
        ret = True if status_code == 0 else False
        if not ret or self.verbose:
            sys.stdout.write(stdout)
            sys.stderr.write(stderr)
            sys.stdout.flush()
            sys.stderr.flush()

        #if tmp_include:
            #os.remove(tmp_include)
        #if tmp_exclude:
            #os.remove(tmp_exclude)
        #if tmp_source:
            #os.remove(tmp_source)
        return ret

    @staticmethod
    def _normalize_url(url):
        o = urlparse.urlparse(url)
        if o.scheme == 'rsync':
            if o.username:
                ret += o.username
                ret += '@'
            ret = o.hostname
            ret += ':'
            ret += o.path
        else:
            ret = url
        return ret
    
    @staticmethod
    def is_rsync_url(url):
        o = urlparse.urlparse(url)
        return True if o.scheme == 'rsync' else False

if __name__ == "__main__":
    app = Rsync(sys.argv[1], sys.argv[2])

    if app.execute():
        print('successful')
    else:
        print('failed')
