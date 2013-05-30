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
