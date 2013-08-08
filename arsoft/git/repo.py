#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import sys
from arsoft.utils import runcmdAndGetData, to_uid, to_gid, enum
from arsoft.inifile import IniFile
from .base import GIT_EXECUTABLE, GIT_HOOKS

class GitRepository(object):

    SubmoduleStatus = enum(Invalid=-1, Ok=0, NotInitialized=1, CommitMismatch=2, MergeConflict=3)
    
    def __init__(self, directory, name=None, bare=False, verbose=False):
        self._name = name
        self.root_directory = directory
        if os.path.isdir(directory):
            self.bare = self.is_bare_repository(directory)
        else:
            self.bare = bare
        self.verbose = verbose
        self._last_error = None
        if self.bare:
            self.magic_directory = self.root_directory
        else:
            self.magic_directory = os.path.join(self.root_directory, '.git')
            
    def __str__(self):
        return 'GitRepository(%s in %s)' %(self._name, self.root_directory)

    @staticmethod
    def is_regular_repository(path):
        if os.path.isdir(os.path.join(path, '.git')):
            return True
        else:
            return False

    @staticmethod
    def is_submodule_repository(path):
        if os.path.isfile(os.path.join(path, '.git')):
            return True
        else:
            return False

    @staticmethod
    def is_bare_repository(path):
        # check for bare GIT repo
        if os.path.isfile(os.path.join(path, 'config')) and os.path.isfile(os.path.join(path, 'HEAD')) and os.path.isdir(os.path.join(path, 'objects')):
            return True
        else:
            return False

    @staticmethod
    def find_repository_root(path):
        while True:
            if GitRepository.is_regular_repository(path):
                return path
            elif GitRepository.is_submodule_repository(path):
                return path
            elif GitRepository.is_bare_repository(path):
                return path
            else:
                (head, tail) = os.path.split(path)
                if head != path:
                    path = head
                else:
                    break
        return None

    @property
    def valid(self):
        if os.path.isdir(self.root_directory):
            if self.bare:
                ret = self.is_bare_repository(self.root_directory)
                if not ret:
                    self._last_error = '%s is not a bare GIT repository' % (self.root_directory)
            else:
                ret = self.is_regular_repository(self.root_directory)
                if not ret:
                    self._last_error = '%s is not a regular GIT repository' % (self.root_directory)
        else:
            ret = False
            self._last_error = 'invalid directory %s for GIT repository' % (self.root_directory)
        return ret
    @property
    def name(self):
        if self._name is None:
            (bname, bext) = os.path.splitext(os.path.basename(self.root_directory))
            self._name = bname
        return self._name

    @property
    def last_error(self):
        return self._last_error

    @property
    def path(self):
        return self.root_directory

    @property
    def hook_directory(self):
        return os.path.join(self.magic_directory, 'hooks')

    @property
    def exclude_file(self):
        return os.path.join(self.magic_directory, 'info', 'exclude')

    @property
    def description(self):
        desc_file = os.path.join(self.magic_directory, 'description')
        try:
            f = open(desc_file, 'r')
            ret = f.read()
            f.close()
        except IOError:
            ret = None
        return ret

    @description.setter
    def description(self, value):
        desc_file = os.path.join(self.magic_directory, 'description')
        f = open(desc_file, 'w')
        f.write(value)
        f.close()

    @staticmethod
    def is_magic_dir(directory):
        if os.path.isdir(directory):
            packed_refs_file = os.path.join(directory, 'packed-refs')
            objects_dir = os.path.join(directory, 'objects')
            if os.path.isfile(packed_refs_file) and os.path.isdir(objects_dir):
                ret = True
            else:
                ret = False
        else:
            ret = False
        return ret

    def is_export_ok(self, export_ok_file='git-daemon-export-ok'):
        path = os.path.join(self.magic_directory, export_ok_file)
        return os.path.isfile(path)

    def set_export_ok(self, enable=True, export_ok_file='git-daemon-export-ok'):
        path = os.path.join(self.magic_directory, export_ok_file)
        if enable:
            if os.path.isfile(path):
                ret = True
            else:
                try:
                    f = open(path, 'w')
                    f.close()
                    ret = True
                except IOError:
                    ret = False
        else:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    ret = True
                except IOError:
                    ret = False
            else:
                ret = True
        return ret

    @staticmethod
    def find_repository(start_dir):
        current_dir = os.path.abspath(os.path.realpath(start_dir))
        ret = None
        while ret is None:
            git_magic_dir = os.path.join(current_dir, '.git')
            if GitRepository.is_magic_dir(git_magic_dir):
                ret = current_dir
            elif os.path.isfile(git_magic_dir):
                # found a .git file which is used by a submodule and 
                # points to the magic directory of the submodule
                submodule_magic_dir = None
                try:
                    f = open(git_magic_dir, 'r')
                    first_line = f.readline()
                    if first_line.startswith('gitdir:'):
                        submodule_magic_dir = os.path.abspath(os.path.normpath(os.path.join(current_dir, first_line[8:])))
                except IOError:
                    pass
                if submodule_magic_dir:
                    submodules_dir = os.path.dirname(submodule_magic_dir)
                    if os.path.basename(submodules_dir) == 'modules':
                        submodules_parent_dir = os.path.dirname(submodules_dir)
                        if GitRepository.is_magic_dir(submodules_parent_dir):
                            ret = os.path.dirname(submodules_parent_dir)
            else:
                next_current_dir = os.path.abspath(os.path.normpath(os.path.join(current_dir, '..')))
                if next_current_dir == current_dir:
                    break
                else:
                    (drive, path) = os.path.splitdrive(next_current_dir)
                    #print('next current_dir=%s -> %s, %s'%(next_current_dir,drive, path) )
                    if len(path) == 0:
                        # reached the root directory
                        break
                    else:
                        current_dir = next_current_dir
        return ret

    def git(self, args, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, use_root_for_cwd=True):
        return runcmdAndGetData(GIT_EXECUTABLE, args, cwd=(self.root_directory if use_root_for_cwd else None), verbose=self.verbose, 
                                outputStdErr=outputStdErr, outputStdOut=outputStdErr,
                                stdin=stdin, stdout=stdout, stderr=stderr)

    def clone(self, url, dest_dir=None, recursive=True, branch=None, origin=None, outputStdErr=True, outputStdOut=True):
        args = ['clone']
        if recursive:
            args.append('--recursive')
        if branch:
            args.append('--branch')
            args.append(branch)
        if origin:
            args.append('--origin')
            args.append(origin)
        args.append(url)
        if dest_dir is not None:
            args.append(dest_dir)
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr, use_root_for_cwd=False)

    @property
    def last_commit(self):
        (sts, stdoutdata, stderrdata) = self.git(['rev-parse', 'HEAD'])
        if sts == 0:
            ret = stdoutdata.decode("utf-8").strip()
        else:
            self._last_error = 'Unable to determine (error %i, %s)'%(sts, stderrdata.decode("utf-8").strip())
            ret = None
        return ret

    def pull(self, rebase=True, recursive=True, outputStdErr=True, outputStdOut=True):
        args = ['pull']
        if rebase:
            args.append('--rebase')
        if recursive:
            args.append('--recurse-submodules')
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    def submodule_init(self):
        args = ['submodule', 'init']
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    def submodule_update(self, recursive=True, remote=True):
        args = ['submodule', 'update']
        if recursive:
            args.append('--recursive')
        if remote:
            args.append('--remote')
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    def submodule_status(self, recursive=False):
        args = ['submodule', 'status']
        if recursive:
            args.append('--recursive')
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = []
            stdoutdata = stdoutdata.decode("utf-8")
            for line in stdoutdata.splitlines():
                if line[0] == '-':
                    elems = line.rstrip().split(' ')
                    submodule_name = elems[0][1:]
                    submodule_status = self.SubmoduleStatus.NotInitialized
                elif line[0] == '+':
                    submodule_name = elems[0][1:]
                    submodule_status = self.SubmoduleStatus.CommitMismatch
                elif line[0] == 'U':
                    submodule_name = elems[0][1:]
                    submodule_status = self.SubmoduleStatus.MergeConflict
                else:
                    submodule_status = self.SubmoduleStatus.Ok
                    submodule_name = elems[0]
                submodule_path = elems[1]
                ret.append( (submodule_name, submodule_path, submodule_status) )
        else:
            ret = None
        return ret
    
    def _branch(self):
        args = ['branch', '-a']
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    @property
    def current_branch(self):
        args = ['branch']
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = None
            stdoutdata = stdoutdata.decode("utf-8")
            for line in stdoutdata.splitlines():
                if line[0] == '*':
                    elems = line.lstrip().split(' ')
                    ret = None if '(no branch)' in line else elems[1]
        else:
            ret = None
        return ret

    def branches(self, remotes=True, local=True):
        args = ['branch']
        if remotes and local:
            args.append('-a')
        elif remotes:
            args.append('-r')
        else:
            pass
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = []
            stdoutdata = stdoutdata.decode("utf-8")
            for line in stdoutdata.splitlines():
                if '(no branch)' in line or 'HEAD' in line:
                    continue
                
                elems = line.lstrip().split(' ')
                if elems[0] == '*':
                    branch_name = elems[1]
                else:
                    branch_name = elems[0]
                is_remote = True if branch_name.startswith('remotes/') else False

                if is_remote:
                    if remotes:
                        ret.append(branch_name)
                else:
                    if local:
                        ret.append(branch_name)
        else:
            ret = None
        return ret
    
    def checkout(self, branch, remote='origin'):
        if branch != self.current_branch:
            args = ['checkout']
            if branch in self.branches(remotes=False, local=True):
                args.append(branch)
            else:
                args.append('-b')
                args.append(branch)
                args.append(remote + '/' + branch)
            return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
        else:
            return (0, None, None)

    def create_branch(self, branch, start_point=None):
        args = ['branch']
        args.append(branch)
        if start_point:
            args.append(start_point)
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)

    def create_tag(self, tag, object_or_commit='HEAD', force=False):
        args = ['tag']
        args.append(tag)
        if force:
            args.append('-f')
        args.append(object_or_commit)
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)

    def create_bundle(self, filename, rev_list=[], all=True):
        args = ['bundle', 'create', filename]
        if all:
            args.append('--all')
        args.extend(rev_list)
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)

    def update_config(self, configfile):
        try:
            ret = True
            f = open(configfile, 'r')
            for line in f:
                line = line.rstrip()
                if len(line) == 0 or line[0] == '#':
                    continue
                
                if '=' in line:
                    (name, value) = line.split('=', 2)
                
                    args = ['config']
                    if value == '<<unset>>':
                        args.extend(['--unset', name])
                    else:
                        args.extend([name, value])

                    (sts, stdoutdata, stderrdata) = self.git(args, stdout=sys.stdout, stderr=sys.stderr)
                    if sts != 0:
                        ret = False
            f.close()
        except IOError:
            ret = False
        return ret
    
    def _fix_permissions_impl(self, directory, uid, gid, dir_perms, file_perms):
        if os.path.isdir(directory):
            try:
                os.chown(directory, uid, gid)
                os.chmod(directory, dir_perms)
                ret = True
            except IOError as e:
                self._last_error = str(e)
                ret = False
            if ret:
                for item in os.listdir(directory):
                    path = os.path.join(directory, item)
                    ret = self._fix_permissions_impl(path, uid, gid, dir_perms, file_perms)
                    if not ret:
                        break
        elif os.path.isfile(directory):
            try:
                os.chown(directory, uid, gid)
                os.chmod(directory, file_perms)
                ret = True
            except IOError as e:
                self._last_error = str(e)
                ret = False
        else:
            # ignore symlinks and other stuff
            ret = True
        return ret
    
    def fix_permissions(self, owner=None, group=None, dir_perms=0775, file_perms=0664 ):
        
        uid = to_uid(owner) if owner else None
        gid = to_gid(group) if group else None
        
        ret = True
        # fix perms for selected directories
        for d in ['branches', 'info', 'logs', 'objects', 'refs' ]:
            dir_path = os.path.join(self.magic_directory, d)
            if os.path.isdir(dir_path):
                ret = self._fix_permissions_impl(dir_path, uid, gid, dir_perms, file_perms)
                if not ret:
                    break
        for hook in GIT_HOOKS:
            file_path = os.path.join(self.hook_directory, d)
            if os.path.isfile(file_path):
                ret = self._fix_permissions_impl(file_path, uid, gid, dir_perms, 0775)
                if not ret:
                    break

        # fix perms for selected files
        for f in ['config', 'description', 'packed-refs', 'git-daemon-export-ok', 'HEAD', 'revlist', 'commitlist' ]:
            file_path = os.path.join(self.magic_directory, f)
            if os.path.isfile(file_path):
                ret = self._fix_permissions_impl(file_path, uid, gid, dir_perms, file_perms)
                if not ret:
                    break
        return ret

    @property
    def excludes(self):
        exclude_file = os.path.join(self.magic_directory, 'info', 'exclude')
        inifile = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False, keyIsWord=False)
        inifile.open(exclude_file)

        ret = []
        main_section = inifile.section(None)
        if main_section:
            for (key, raw_value) in main_section.get_all():
                if key is None:
                    continue
                attr_params = {}
                ret.append( key )
        inifile.close()
        return ret

    @excludes.setter
    def excludes(self, value):
        exclude_file = os.path.join(self.magic_directory, 'info', 'exclude')
        inifile = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False, keyIsWord=False)
        inifile.open(exclude_file)

        for key in value:
            inifile.set(None, key, '')
        return inifile.save(exclude_file)

    @property
    def attributes(self):
        attributes_file = os.path.join(self.magic_directory, 'info', 'attributes')
        inifile = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False, keyIsWord=False)
        inifile.open(attributes_file)

        ret = []
        main_section = inifile.section(None)
        if main_section:
            for (key, raw_value) in main_section.get_all():
                if key is None:
                    continue
                attr_params = {}
                for pair in raw_value.split(' '):
                    if '=' in pair:
                        (pair_key, pair_value) = pair.split('=')
                    else:
                        pair_key = pair
                        pair_value = None
                    attr_params[pair_key] = pair_value
                ret.append( (key, attr_params) )
        inifile.close()
        return ret

    @attributes.setter
    def attributes(self, value):
        attributes_file = os.path.join(self.magic_directory, 'info', 'attributes')
        inifile = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False, keyIsWord=False)
        inifile.open(attributes_file)

        for (key, params) in value:
            str_params = []
            for (param_key, param_value) in params.iteritems():
                if param_value is None:
                    str_params.append(param_key)
                else:
                    str_params.append(param_key + '=' + param_value)
            inifile.set(None, key, ' '.join(str_params))
        return inifile.save(attributes_file)

if __name__ == '__main__':

    DEFAULT_EXCLUDES = [
        # executable or compiler result files
        '*.com', '*.class', '*.dll', '*.exe', '*.o', '*.obj', '*.so', '*.pyc',
        # backup files
        '*~', '*.bak',
        # package files
        '*.7z', '*.dmg', '*.deb', '*.gz', '*.bz2', '*.xz', '*.iso', '*.jar', '*.rar', '*.tar', '*.zip',
        # log files
        '*.log',
        # database files
        '*.db', '*.sqlite',
        # OS generated files or search helpers
        '.DS_Store*', '._*', '.Spotlight-V100', '.Trashes', 'Icon?', 'ehthumbs.db', 'Thumbs.db',
        ]
    
    DEFAULT_ATTIRBUTES = [
        ('*.png', {'diff':'exif'} ),
        ('*.jpg', {'diff':'exif'} ),
        ('*.gif', {'diff':'exif'} ),
        ('*.svg', {'diff':'exif'} ),
        ('*.tif', {'diff':'exif'} ),
        ('*.tiff', {'diff':'exif'} ),
        ('*.pdf', {'diff':'exif'} ),
        ('*.zip', {'diff':'zip'} ),
        ('*.odt', {'diff':'odt'} ),
        ('*.odp', {'diff':'odt'} ),
        ('*.ods', {'diff':'odt'} ),
        ('*.odg', {'diff':'odt'} ),
        # some well known binary extensions
        ('*.jar', {'binary':None} ),
        ('*.so', {'binary':None} ),
        ('*.dll', {'binary':None} ),
        # ensure LF endings on all checkouts
        ('configure.in', {'crlf':'input'} ),
        # text formats with special handling/needs
        ('*.sh', {'eol':'lf'} ),
        ('*.bat', {'eol':'crlf'} ),
        ('*.sln', {'eol':'crlf'} ),
        ('*.*proj*', {'eol':'crlf'} ),
        ]
        
    repo = GitRepository(sys.argv[1])
    
    print('git: %s' % (GIT_EXECUTABLE))
    print('path: %s' % (str(repo.path)))
    print('name: %s' % (str(repo.name)))
    print('bare: %s' % (str(repo.bare)))
    print('magic: %s' % (str(repo.magic_directory)))
    print('description: %s' % (str(repo.description)))
    print('current branch: %s' % (str(repo.current_branch)))
    print('attributes: %s' % (str(repo.attributes)))
    print('excludes: %s' % (str(repo.excludes)))
    
    repo.attributes = DEFAULT_ATTIRBUTES
    repo.excludes = DEFAULT_EXCLUDES
