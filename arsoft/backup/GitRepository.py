#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from BaseRepository import *

class GitRepository(BaseRepository):

    def __init__(self, path, verbose=False, git_executable='/usr/bin/git'):
        BaseRepository.__init__(self, path, verbose)
        self._git_executable = git_executable
        self._is_bare_directory = None

    def _determine_directory_type(self):
        if self._is_bare_directory is None:
            if GitRepository.is_bare_repository(self._path):
                self._is_bare_directory = True
            else:
                self._is_bare_directory = False

    @staticmethod
    def is_valid(path):
        while True:
            if GitRepository.is_regular_repository(path):
                return True
            elif GitRepository.is_bare_repository(path):
                return True
            else:
                (head, tail) = os.path.split(path)
                if head != path:
                    path = head
                else:
                    break
        return False

    @staticmethod
    def is_regular_repository(path):
        if os.path.isdir(os.path.join(path, '.git')):
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

    def create(self, **kwargs):
        if 'bare' in kwargs:
            bare = kwargs['bare']
        else:
            bare = False
        args = ['init', self._path]
        if bare:
            args.append('--bare')

        return arsoft.utils.runcmd(self._git_executable, args, verbose=self.m_verbose)

    def get_current_revision(self):
        self._determine_directory_type()
        (ret, stdout, stderr) = arsoft.utils.runcmdAndGetData(self._git_executable, ['rev-parse', 'HEAD', self._path], verbose=self._verbose)
        if ret == 0 and stdout is not None and len(stdout):
            ret = stdout
        else:
            ret = None
        return ret
