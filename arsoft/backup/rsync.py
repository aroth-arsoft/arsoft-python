#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import tempfile
from FileList import *
from arsoft.utils import runcmd
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
        args = [self._rsync_bin]
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
            tmp_include = tempfile.NamedTemporaryFile()
            if not self._include.save(tmp_include):
                raise IOError
            args.append('--include-from=' + tmp_include.name)

        if self._exclude:
            tmp_exclude = tempfile.NamedTemporaryFile()
            if not self._exclude.save(tmp_exclude):
                raise IOError
            args.append('--exclude-from=' + tmp_exclude.name)

        if isinstance(self._source, FileList):
            tmp_source = tempfile.NamedTemporaryFile()
            if not self._source.save(tmp_source):
                raise IOError
            args.append('--files-from=' + tmp_source.name)
        else:
            args.append(self._source)
        args.append(self._dest)

        if self.verbose:
            print("runcmd " + ' '.join(args))

        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
        if p:
            (stdoutdata, stderrdata) = p.communicate()
            if stdoutdata is not None:
                if int(python_major) < 3: # check for version < 3
                    sys.stdout.write(stdoutdata)
                    sys.stdout.flush()
                else:
                    sys.stdout.buffer.write(stdoutdata)
                    sys.stdout.buffer.flush()
            if stderrdata is not None:
                if int(python_major) < 3: # check for version < 3
                    sys.stderr.write(stderrdata)
                    sys.stderr.flush()
                else:
                    sys.stderr.buffer.write(stderrdata)
                    sys.stderr.buffer.flush()
            status_code = p.returncode
            ret = True if status_code == 0 else False
        else:
            status_code = -1
            ret = False

        if tmp_include:
            tmp_include.close()
        if tmp_exclude:
            tmp_exclude.close()
        if tmp_source:
            tmp_source.close()
        return ret

if __name__ == "__main__":
    app = Rsync(sys.argv[1], sys.argv[2])

    if app.execute():
        print('successful')
    else:
        print('failed')
