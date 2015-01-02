#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import sys
from arsoft.utils import runcmdAndGetData, to_uid, to_gid, enum
from .base import GIT_EXECUTABLE
from .error import *

class GitBundle(object):

    def __init__(self, filename, repository=None, verbose=False):
        self._filename = filename
        self._repository = repository
        self.verbose = verbose
            
    def __str__(self):
        return 'GitBundle(%s)' %(self._filename)

    def git(self, args, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, use_root_for_cwd=True, cwd=None):
        if cwd is not None:
            use_cwd = cwd
        elif self._repository:
            if use_root_for_cwd:
                use_cwd = self._repository.root_directory
            else:
                use_cwd = None
        else:
            use_cwd = None
        return runcmdAndGetData([GIT_EXECUTABLE] + args, cwd=use_cwd, verbose=self.verbose,
                                outputStdErr=outputStdErr, outputStdOut=outputStdErr,
                                stdin=stdin, stdout=stdout, stderr=stderr)

    @staticmethod
    def is_bundle(path):
        args = [GIT_EXECUTABLE, 'bundle', 'list-heads', path ]
        (sts, stdout, stderr) = runcmdAndGetData(args)
        if sts == 0:
            return True
        else:
            return False

    @staticmethod
    def create(repository, filename, rev_list=[], all=True):
        args = [GIT_EXECUTABLE, 'bundle', 'create', filename]
        if all:
            args.append('--all')
        args.extend(rev_list)
        if isinstance(repository, GitRepository):
            cwd = repository.root_directory
            repo = repository
        else:
            cwd = repository
            repo = GitRepository(repository)
        (sts, stdout, stderr) = runcmdAndGetData(args, cwd=cwd)
        if sts == 0:
            return GitBundle(filename, repository=repo)
        else:
            raise GitRepositoryError(repo, sts, stdout, stderr)

    def _recreate(self, rev_list=[], repository=None, all=True):
        if repository is None:
            repository = self._repository
        args = [GIT_EXECUTABLE, 'bundle', 'create', self._filename]
        if all:
            args.append('--all')
        args.extend(rev_list)
        (sts, stdout, stderr) = runcmdAndGetData(args, cwd=repository.root_directory)
        if sts == 0:
            return True
        else:
            raise GitBundleError(repo, sts, stdout, stderr)

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
    def filename(self):
        return self._filename

    @property
    def repository(self):
        return self._repository

    def _list_heads(self):
        (sts, stdoutdata, stderrdata) = self.git(['bundle', 'list-heads', self._filename])
        if sts == 0:
            ret = {}
            all_data = stdoutdata.decode("utf-8").strip()
            for line in all_data.splitlines():
                (sha1, name) = line.split(' ', 1)
                ret[name] = sha1
        else:
            raise GitBundleError(self, sts, stdoutdata, stderrdata)
        return ret

    @property
    def heads(self):
        return self._list_heads()

    def update(self, repository=None):
        if repository is None:
            repository = self._repository

        bundle_heads = self._list_heads()
        repo_heads = repository.list_heads(remotes=False)
        recreate_required = False
        for (ref_name, repo_sha1) in repo_heads.items():
            if ref_name in bundle_heads:
                # ref_name was previously included in the bundle, so just update it
                bundle_sha1 = bundle_heads[ref_name]
                if repo_sha1 != bundle_sha1:
                    # but the sha1 does not match so something changed
                    recreate_required = True
            else:
                # new head appears in repo, so we need to put it the bundle
                recreate_required = True
        if recreate_required:
            ret = self._recreate(repository)
        else:
            ret = True
        return ret

    def verify(self, outputStdErr=True, outputStdOut=True):
        args = ['bundle', 'verify']
        return self.git(args, stdout=sys.stdout, stderr=sys.stderr)

if __name__ == '__main__':

    bundle = GitBundle(sys.argv[1])

    print('git: %s' % (GIT_EXECUTABLE))
    print('filename: %s' % (str(bundle.filename)))
    print('valid: %s' % (str(bundle.valid)))
    print('heads: %s' % (str(bundle.heads)))
