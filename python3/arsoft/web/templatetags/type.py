#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from django import template

register = template.Library()

def do_type(expr):
    return type(expr)

register.filter('type', do_type)
 
