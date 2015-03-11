#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import tempfile
from .filelist import *
from .utils import runcmdAndGetData
import urllib.parse
import sys

class RsyncDefaults(object):
    RSYNC_BIN = '/usr/bin/rsync'

class Rsync(object):
    def __init__(self, source, dest, include=None, exclude=None, linkDest=None,
                 recursive=True, relative=False,
                 preservePermissions=True, preserveOwner=True, preserveGroup=True, preserveTimes=True, 
                 preserveDevices=True, preserveSpecials=True, perserveACL=False, preserveXAttrs=False,
                 numericIds=True,
                 verbose=False, compress=True, links=True, dryrun=False,
                 delete=False, deleteExcluded=False, force=False, delayUpdates=False,
                 rsh=None, bandwidthLimit=None,
                 use_ssh=False, ssh_key=None,
                 rsync_bin=RsyncDefaults.RSYNC_BIN):
        self._rsync_bin = rsync_bin
        self._source = source
        self._dest = dest
        self.linkDest = linkDest
        self.verbose = verbose
        self.recursive = recursive
        self.relative = relative
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
        self.numericIds = numericIds
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

    def execute(self, stdout=None, stderr=None, stderr_to_stdout=False):
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
        if self.relative:
            args.append('--relative')
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
            args.append('--delete-excluded')
        if self.force:
            args.append('--force')
        if self.delayUpdates:
            args.append('--delay-updates')
        if self.dryrun:
            args.append('--dry-run')
        if self.numericIds:
            args.append('--numeric-ids')
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
                print('Include=[%s]' % self._include)

        if self._exclude:
            tmp_fd, tmp_exclude = tempfile.mkstemp()
            tmp_fobj = os.fdopen(tmp_fd, 'w')
            if not self._exclude.save(tmp_fobj):
                raise IOError
            tmp_fobj.close()
            args.append('--exclude-from=' + tmp_exclude)
            if self.verbose:
                print('Exclude=[%s]' % self._exclude)

        if self.linkDest:
            linkDest_url = Rsync.parse_url(self.linkDest)
            if linkDest_url:
                args.append('--link-dest=' + linkDest_url.path)
            else:
                args.append('--link-dest=' + self.linkDest)

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
                print('Source=[%s]' % self._source)
        else:
            args.append(self._source)
        args.append(self._normalize_url(self._dest))

        (status_code, stdout_data, stderr_data) = runcmdAndGetData([self._rsync_bin] + args, stdout=stdout, stderr_to_stdout=stderr_to_stdout, verbose=self.verbose)
        ret = True if status_code == 0 else False

        if tmp_include:
            os.remove(tmp_include)
        if tmp_exclude:
            os.remove(tmp_exclude)
        if tmp_source:
            os.remove(tmp_source)
        return ret

    @staticmethod
    def _normalize_url(url):
        o = urllib.parse.urlparse(url)
        if o.scheme == 'rsync':
            ret = ''
            if o.username:
                ret += o.username
                ret += '@'
            ret += o.hostname
            ret += ':'
            ret += o.path
        else:
            ret = url
        return ret

    @staticmethod
    def is_rsync_url(url):
        o = urllib.parse.urlparse(url)
        return True if o.scheme == 'rsync' else False

    @staticmethod
    def parse_url(url):
        o = urllib.parse.urlparse(url)
        if o.scheme == 'rsync':
            return o
        else:
            return None

    @staticmethod
    def join_url(base, url):
        if isinstance(base, tuple):
            ret = ''
            if base.scheme == 'rsync':
                ret = 'rsync://'
                if base.username:
                    ret += base.username
                    if base.password:
                        ret += ':' + base.password
                    ret += '@'
                ret += base.hostname
                ret += os.path.join(base.path, url)
            return ret
        else:
            return urllib.parse.urljoin(base, url)
        
    @staticmethod
    def is_link_dest_valid(destination, link_dest_dir):
        if '://' in destination:
            url_destination = urllib.parse.urlparse(destination)
        else:
            url_destination = None
        if link_dest_dir and '://' in link_dest_dir:
            url_link_dest = urllib.parse.urlparse(link_dest_dir)
        else:
            url_link_dest = None
        if url_destination and url_link_dest:
            if url_destination.scheme == 'rsync' and url_link_dest.scheme == 'rsync' and \
                url_destination.hostname == url_link_dest.hostname:
                    ret = True
            else:
                ret = False
        else:
            ret = True
        return ret

    @staticmethod
    def sync_directories(source_dir, target_dir, recursive=True, relative=True, exclude=None, delete=True, deleteExcluded=True, stdout=None, stderr=None, stderr_to_stdout=False, verbose=False):
        r = Rsync(source=source_dir, dest=target_dir, recursive=recursive, relative=relative, exclude=exclude, delete=delete, deleteExcluded=deleteExcluded, verbose=verbose)
        return r.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)

    @staticmethod
    def sync_file(source_file, target_file, relative=True, exclude=None, stdout=None, stderr=None, stderr_to_stdout=False, verbose=False):
        # first we must create the target directory
        target_dir = os.path.dirname(target_file)
        if target_dir[-1] != '/':
            target_dir += '/'
        rdir = Rsync(source='/dev/null', dest=target_dir, recursive=False, relative=False, verbose=verbose)
        if rdir.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout):
            # when the directory exists we can copy the file
            r = Rsync(source=source_file, dest=target_file, recursive=False, relative=False, verbose=verbose, exclude=exclude)
            return r.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)
        else:
            return False

if __name__ == "__main__":
    app = Rsync(sys.argv[1], sys.argv[2])

    if app.execute():
        print('successful')
    else:
        print('failed')
