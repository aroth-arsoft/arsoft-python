#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import sys
from arsoft.utils import runcmdAndGetData
from arsoft.inifile import IniFile
from base import GIT_EXECUTABLE

class GitRepository(object):

    def __init__(self, directory, name=None, bare=False, verbose=False):
        self.name = name
        self.root_directory = directory
        if os.path.isdir(directory):
            self.bare = self.is_bare_repository(directory)
        else:
            self.bare = bare
        self.verbose = verbose
        if self.bare:
            self.magic_directory = self.root_directory
        else:
            self.magic_directory = os.path.join(self.root_directory, '.git')
            
    def __str__(self):
        return '%s in %s' %(self.name, self.root_directory)

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
        gitpath = os.path.join(path, 'config')
        if os.path.isfile(os.path.join(path, 'config')) and os.path.isfile(os.path.join(path, 'revlist')):
            return True
        else:
            return False

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

    def git(self, args, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None):
        return runcmdAndGetData(GIT_EXECUTABLE, args, cwd=self.root_directory, verbose=self.verbose, 
                                outputStdErr=outputStdErr, outputStdOut=outputStdErr,
                                stdin=stdin, stdout=stdout, stderr=stderr)

    @property
    def last_commit(self):
        (sts, stdoutdata, stderrdata) = self.git(['rev-parse', 'HEAD'])
        if sts == 0:
            ret = stdoutdata.strip()
        else:
            ret = None
        return ret

    def pull(self, rebase=True, recursive=True, outputStdErr=True, outputStdOut=True):
        args = ['pull']
        if rebase:
            args.append('--rebase')
        if recursive:
            args.append('--recurse-submodules')
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    def submodule_update(self, recursive=True, remote=True):
        args = ['submodule', 'update']
        if recursive:
            args.append('--recursive')
        if remote:
            args.append('--remote')
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    def _branch(self):
        args = ['branch', '-a']
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)
    
    @property
    def current_branch(self):
        args = ['branch']
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = None
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
