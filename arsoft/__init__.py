#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

# this is a namespace package
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from .ifconfig import ifconfig
from .inifile import IniFile, IniSection
from .utils import *
