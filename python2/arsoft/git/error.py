#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class GitError(Exception):
    def __init__(self, status=0, stdout=None, stderr=None):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return self.stderr

class GitRepositoryError(GitError):
    def __init__(self, repository=None, status=0, stdout=None, stderr=None):
        GitError.__init__(self, status, stdout, stderr)
        self.repository = repository
        
class GitBundleError(GitError):
    def __init__(self, bundle=None, status=0, stdout=None, stderr=None):
        GitError.__init__(self, status, stdout, stderr)
        self.bundle = bundle

