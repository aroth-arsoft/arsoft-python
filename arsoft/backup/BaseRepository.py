#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import os
import subprocess
import arsoft.utils

class BaseRepository:

    def __init__(self, path, verbose=False):
        self._path = path
        self._verbose = verbose

    def log(self, msg):
        if self._verbose:
            print(str(msg))
            
    @staticmethod
    def is_valid(path):
        raise NotImplementedError("Derived class must implement this.")

    def create(self, **kwargs):
        raise NotImplementedError("Derived class must implement this.")
    
    def get_current_revision(self):
        raise NotImplementedError("Derived class must implement this.")

    def dump(self, bakfile, minrev=None, maxrev=None):
        raise NotImplementedError("Derived class must implement this.")

    @property
    def path(self):
        return self._path

    @property
    def current_revision(self):
        return self.get_current_revision()
