#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import which

def find_git_executable():
    candidates = which('git')
    if len(candidates) > 0:
        return candidates[0]
    else:
        return None

GIT_EXECUTABLE = find_git_executable()

GIT_SERVER_HOOKS = ['pre-receive', 'post-receive', 'update', 'post-update']
GIT_CLIENT_HOOKS = ['applypatch-msg', 
                    'pre-applypatch', 
                    'post-applypatch', 
                    'pre-commit', 
                    'prepare-commit-msg', 
                    'commit-msg',
                    'post-commit', 
                    'pre-rebase',
                    'post-checkout',
                    'post-merge',
                    'pre-auto-gc'
                    'post-rewrite']
GIT_HOOKS = GIT_SERVER_HOOKS + GIT_CLIENT_HOOKS
