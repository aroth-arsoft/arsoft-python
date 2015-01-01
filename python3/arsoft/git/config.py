#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import sys
import yaml
from arsoft.utils import runcmdAndGetData
from .repo import *

class GitConfig(object):
    def __init__(self, repo=None, verbose=False):
        self._repo = repo
        self.verbose = verbose
        self._root_directory = repo.root_directory if repo else None

    def git(self, args, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None):
        return runcmdAndGetData([GIT_EXECUTABLE] + args, cwd=self._root_directory, verbose=self.verbose,
                                outputStdErr=outputStdErr, outputStdOut=outputStdErr,
                                stdin=stdin, stdout=stdout, stderr=stderr)
        
    def get(self, name, default_value=None):
        args = ['config', name]
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = stdoutdata.decode("utf-8").rstrip('\n')
        else:
            ret = default_value
        return ret

    def set(self, name, value):
        args = ['config']
        if self._repo is not None:
            args.append('--local')
        else:
            args.append('--global')
        args.extend([name, value])
        (sts, stdoutdata, stderrdata) = self.git(args)
        if sts == 0:
            ret = True
        else:
            ret = False
        return ret

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        self.set(name, value)
