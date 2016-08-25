#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

"""Package to wrap legacy mod_python code in WSGI apps."""
import sys
import os.path

__all__ = ['request', 'wrap']

mod_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, mod_dir)
