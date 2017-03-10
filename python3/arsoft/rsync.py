#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import tempfile
from .filelist import *
from .utils import runcmdAndGetData
from .timestamp import strptime_as_timestamp
import urllib.parse
import sys
import stat

class RsyncDefaults(object):
    RSYNC_BIN = '/usr/bin/rsync'

class rsync_stat_result(object):

    @staticmethod
    def str_mode2mode(str):
        if len(str) < 10:
            return None
        ret = 0
        if str[0] == 'd':
            ret += stat.S_IFDIR
        elif str[0] == 's':
            ret += stat.S_IFSOCK
        elif str[0] == 'l':
            ret += stat.S_IFLNK
        else:
            ret += stat.S_IFREG
        if str[1] == 'r':
            ret += stat.S_IRUSR
        if str[2] == 'w':
            ret += stat.S_IWUSR
        if str[3] == 'x':
            ret += stat.S_IXUSR
        if str[4] == 'r':
            ret += stat.S_IRGRP
        if str[5] == 'w':
            ret += stat.S_IWGRP
        if str[6] == 'x':
            ret += stat.S_IXGRP
        if str[7] == 'r':
            ret += stat.S_IROTH
        if str[8] == 'w':
            ret += stat.S_IWOTH
        if str[9] == 'x':
            ret += stat.S_IXOTH
        return ret

    @staticmethod
    def str_size2size(str, base=10, default_value=0):
        try:
            ret = int(str.replace(',', ''), base)
        except ValueError:
            ret = default_value
        return ret

    def __init__(self, mode, size, date, time):
        self.st_mode = rsync_stat_result.str_mode2mode(mode)
        self.st_ino=0
        self.st_dev=0
        self.st_nlink=0
        self.st_uid=0
        self.st_gid=0
        self.st_size = rsync_stat_result.str_size2size(size)
        self.st_atime=0
        self.st_mtime = strptime_as_timestamp(date + ' ' + time, '%Y/%m/%d %H:%M:%S')
        self.st_ctime=0

    def __str__(self):
        return 'rsync_stat_result(st_mode=%i, st_ino=%i, st_dev=%i, st_nlink=%i, st_uid=%i, st_gid=%i, st_size=%i, st_atime=%i, st_mtime=%i, st_ctime=%i)' % (
            self.st_mode,
            self.st_ino,
            self.st_dev,
            self.st_nlink,
            self.st_uid,
            self.st_gid,
            self.st_size,
            self.st_atime,
            self.st_mtime,
            self.st_ctime
            )

class Rsync(object):
    def __init__(self, source, dest, include=None, exclude=None, linkDest=None,
                 recursive=True, relative=False,
                 preservePermissions=True, preserveOwner=True, preserveGroup=True, preserveTimes=True, 
                 preserveDevices=True, preserveSpecials=True, perserveACL=False, preserveXAttrs=False,
                 numericIds=True,
                 verbose=False, compress=True, links=True, dryrun=False,
                 delete=False, deleteExcluded=False, force=False, delayUpdates=False,
                 listOnly=False, pruneEmptyDirs=False, stats=False,
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
        self.listOnly = listOnly
        self.stats = stats
        self.pruneEmptyDirs = pruneEmptyDirs
        self._include = include
        self._exclude = exclude

    def executeRaw(self, stdout=None, stderr=None, stderr_to_stdout=False):

        if self.listOnly == False:
            if self._source is None or \
                (isinstance(self._source, str) and len(self._source) == 0) or \
                (isinstance(self._source, FileList) and self._source.empty()):
                raise ValueError('invalid source file or directory %s'%(str(self._source)))

        if self._dest is None or \
            (isinstance(self._dest, str) and len(self._dest) == 0) or \
            (isinstance(self._dest, FileList) and self._dest.empty()):
            raise ValueError('invalid destination file or directory %s'%(str(self._dest)))

        if self._include is not None and not \
            (   isinstance(self._include, str) or \
                isinstance(self._include, list) or \
                isinstance(self._include, FileList) ):
            raise ValueError('invalid include filelist %s'%(str(self._include)))

        if self._exclude is not None and not \
            (   isinstance(self._exclude, str) or \
                isinstance(self._exclude, list) or \
                isinstance(self._exclude, FileList) ):
            raise ValueError('invalid exclude filelist %s'%(str(self._exclude)))

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
        if self.listOnly:
            args.append('--list-only')
        if self.stats:
            args.append('--stats')
        if self.numericIds:
            args.append('--numeric-ids')
        if self.pruneEmptyDirs:
            args.append('--prune-empty-dirs')

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
            if isinstance(self._include, FileList):
                tmp_fd, tmp_include = tempfile.mkstemp()
                tmp_fobj = os.fdopen(tmp_fd, 'w')
                if not self._include.save(tmp_fobj):
                    raise IOError
                tmp_fobj.close()
                args.append('--include-from=' + tmp_include)
                if self.verbose:
                    print('Include=[%s]' % self._include)
            elif isinstance(self._include, list):
                for arg in self._include:
                    args.append('--include=' + str(arg))
            elif isinstance(self._include, str):
                args.append('--include=' + str(self._include))

        if self._exclude:
            if isinstance(self._exclude, FileList):
                tmp_fd, tmp_exclude = tempfile.mkstemp()
                tmp_fobj = os.fdopen(tmp_fd, 'w')
                if not self._exclude.save(tmp_fobj):
                    raise IOError
                tmp_fobj.close()
                args.append('--exclude-from=' + tmp_exclude)
                if self.verbose:
                    print('Exclude=[%s]' % self._exclude)
            elif isinstance(self._exclude, list):
                for arg in self._exclude:
                    args.append('--exclude=' + str(arg))
            elif isinstance(self._exclude, str):
                args.append('--exclude=' + str(self._exclude))

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
            if not self.listOnly:
                args.append(self._source)
        args.append(self._normalize_url(self._dest))

        rsync_env = os.environ
        rsync_env['LANG'] = 'C'
        (status_code, stdout_data, stderr_data) = runcmdAndGetData([self._rsync_bin] + args, stdout=stdout, stderr_to_stdout=stderr_to_stdout, env=rsync_env, verbose=self.verbose)

        if tmp_include:
            os.remove(tmp_include)
        if tmp_exclude:
            os.remove(tmp_exclude)
        if tmp_source:
            os.remove(tmp_source)
        return (status_code, stdout_data, stderr_data)

    def execute(self, stdout=None, stderr=None, stderr_to_stdout=False):
        (status_code, stdout_data, stderr_data) = self.executeRaw(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)
        return True if status_code == 0 else False

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
    def sync_directories(source_dir, target_dir, recursive=True, relative=True, exclude=None, delete=True, deleteExcluded=True, stdout=None, stderr=None, stderr_to_stdout=False,
                         use_ssh=False, ssh_key=None,
                         verbose=False):
        r = Rsync(source=source_dir, dest=target_dir, recursive=recursive, relative=relative, exclude=exclude,
                  delete=delete, deleteExcluded=deleteExcluded, verbose=verbose,
                  use_ssh=use_ssh, ssh_key=ssh_key)
        return r.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)

    @staticmethod
    def sync_file(source_file, target_file, relative=True, exclude=None, stdout=None, stderr=None, stderr_to_stdout=False,
                  use_ssh=False, ssh_key=None,
                  verbose=False):
        # first we must create the target directory
        target_dir = os.path.dirname(target_file)
        if target_dir[-1] != '/':
            target_dir += '/'
        rdir = Rsync(source='/dev/null', dest=target_dir, recursive=False, relative=False, use_ssh=use_ssh, ssh_key=ssh_key, verbose=verbose)
        if rdir.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout):
            # when the directory exists we can copy the file
            r = Rsync(source=source_file, dest=target_file, recursive=False, relative=False, verbose=verbose, use_ssh=use_ssh, ssh_key=ssh_key, exclude=exclude)
            return r.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)
        else:
            return False

    @staticmethod
    def parse_number(str):
        ret = None
        if ' ' in str:
            elems = str.split(' ')
            try:
                if ',' in elems[0]:
                    elems[0] = elems[0].replace(',','')
                ret = int(elems[0])
            except ValueError:
                pass
        else:
            try:
                if ',' in str:
                    str = str.replace(',','')
                ret = int(str)
            except ValueError:
                pass
        return ret

    @staticmethod
    def listdir(target_dir, use_ssh=False, ssh_key=None, recursive=False, stats=False, verbose=False):
        if target_dir[-1] != '/':
            target_dir += '/'
        rdir = Rsync(source='/dev/null', dest=target_dir, recursive=recursive, relative=False, listOnly=True, stats=stats, use_ssh=use_ssh, ssh_key=ssh_key, verbose=verbose)
        (status_code, stdout_data, stderr_data) = rdir.executeRaw(stdout=None, stderr=None, stderr_to_stdout=False)

        ret = None
        ret_stats = None
        # See http://wpkg.org/Rsync_exit_codes
        # 0 -> successful, 23 -> Partial transfer due to error (e.g. permision denied for some files)
        if status_code == 0 or status_code == 23:
            ret = {}
            ret_stats = {}
            parse_stats = False
            for line in stdout_data.decode('utf-8').splitlines():
                if not line:
                    parse_stats = True
                    continue
                if parse_stats and stats:
                    #print(line)
                    idx = line.find(':')
                    if idx > 0:
                        key = line[0:idx]
                        value = line[idx+1:].strip()
                        skip = False
                        if key == 'Number of files':
                            details = {}
                            # 18 (reg: 4, dir: 12, special: 2)
                            total = 0
                            start = value.find('(')
                            end = value.find(')')
                            if start > 0 and end > 0:
                                total = Rsync.parse_number(value[0:start])
                                for e in value[start+1:end].split(','):
                                    #print(e)
                                    idx = e.find(':')
                                    if idx > 0:
                                        k = e[0:idx].strip()
                                        v = Rsync.parse_number(e[idx+1:].strip())
                                        details[k] = v
                            ret_stats['num_total_files'] = total
                            ret_stats['num_regular_files'] = details.get('reg', 0)
                            ret_stats['num_special_files'] = details.get('special', 0)
                            ret_stats['num_dirs'] = details.get('dir', 0)
                            skip = True
                        elif key == 'Total file size':
                            skip = True
                            ret_stats['total_file_size'] = Rsync.parse_number(value)
                        elif key == 'Total transferred file size':
                            skip = True
                            ret_stats['total_transferred_file_size'] = Rsync.parse_number(value)
                        elif key == 'File list size':
                            skip = True
                            ret_stats['file_list_size'] = Rsync.parse_number(value)
                        elif key.startswith('Total bytes'):
                            skip = True
                            if key == 'Total bytes received':
                                ret_stats['total_bytes_received'] = Rsync.parse_number(value)
                            elif key == 'Total bytes sent':
                                ret_stats['total_bytes_sent'] = Rsync.parse_number(value)
                            else:
                                skip = False
                        elif key.startswith('Number of'):
                            skip = True
                            if key == 'Number of created files':
                                ret_stats['num_created_files'] = Rsync.parse_number(value)
                            elif key == 'Number of deleted files':
                                ret_stats['num_deleted_files'] = Rsync.parse_number(value)
                            elif 'Number of regular files transferred':
                                ret_stats['num_regular_files_transferred'] = Rsync.parse_number(value)
                            else:
                                skip = False

                        if not skip:
                            ret_stats[key] = value
                else:
                    if line.startswith('receiving') or line.startswith('sent') or line.startswith('total size'):
                        continue
                    #print(line)
                    elems = [item for item in line.split(' ') if item]
                    if len(elems) >= 5:
                        mode, size, date, time = elems[0:4]
                        filename = ' '.join(elems[4:])
                        #print(mode, 'size=%s<<' % size, date, time)
                        ret[filename] = rsync_stat_result(mode, size, date, time)
        if stats:
            return ret, ret_stats
        else:
            return ret

    # See https://frickenate.com/2015/09/rsync-deleting-a-remote-directory/
    @staticmethod
    def rmdir(target_dir, recursive=True, force=True, stdout=None, stderr=None, stderr_to_stdout=False,
                  use_ssh=False, ssh_key=None,
                  verbose=False, dryrun=False):
        empty_dir = tempfile.mkdtemp()
        if empty_dir[-1] != '/':
            empty_dir += '/'
        # rsync -vr --delete --include '/dir/***' --exclude='*' $(mktemp -d)/ user@example.com::/module/path/to/
        parent_dir, basename = os.path.split(target_dir)
        if parent_dir[-1] != '/':
            parent_dir += '/'
        rdir = Rsync(source=empty_dir, dest=parent_dir, recursive=recursive, relative=False, use_ssh=use_ssh, ssh_key=ssh_key,
                     delete=True, deleteExcluded=False, pruneEmptyDirs=False,
                     include='%s/***' % basename, exclude='*',
                     preservePermissions=False, preserveOwner=False, preserveGroup=False, preserveTimes=False,
                     preserveDevices=False, preserveSpecials=False, perserveACL=False, preserveXAttrs=False,
                     numericIds=False,
                     force=force, verbose=verbose, dryrun=dryrun)
        ret = rdir.execute(stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout)
        os.rmdir(empty_dir)
        return ret

if __name__ == "__main__":
    #files = Rsync.listdir(sys.argv[1], use_ssh=True, ssh_key=sys.argv[2], verbose=True)
    #if files is not None:
        #for f, s in files.items():
            #print(f, s)
    #app = Rsync(sys.argv[1], sys.argv[2])

    #if app.execute():
        #print('successful')
    #else:
        #print('failed')

    Rsync.rmdir(sys.argv[1], dryrun=False, verbose=True)
