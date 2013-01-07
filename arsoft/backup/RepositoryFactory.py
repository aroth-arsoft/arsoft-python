#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from SubversionRepository import SubversionRepository
from GitRepository import GitRepository
import sys, os
from arsoft.utils import enum

class RepositoryFactory:
    Type = enum(Invalid=-1, Unknown=0, Subversion=1, Git=2)

    @staticmethod
    def detect_type(path):
        if os.path.isdir(path):
            if SubversionRepository.is_valid(path):
                return RepositoryFactory.Type.Subversion
            elif GitRepository.is_valid(path):
                return RepositoryFactory.Type.Git
            else:
                return RepositoryFactory.Type.Unknown
        else:
            return RepositoryFactory.Type.Invalid

    @staticmethod
    def create(path, verbose=False):
        if os.path.isdir(path):
            if SubversionRepository.is_valid(path):
                return SubversionRepository(path, verbose)
            elif GitRepository.is_valid(path):
                return GitRepository(path, verbose)
            else:
                return None
        else:
            return None
 
if __name__ == "__main__":
    print sys.argv[1]
    repo = RepositoryFactory.create(sys.argv[1], verbose=True)
    print repo
    print repo.path
    print repo.current_revision