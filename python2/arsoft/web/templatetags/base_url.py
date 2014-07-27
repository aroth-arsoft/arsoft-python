#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from django import template
from django.core.urlresolvers import get_script_prefix

register = template.Library()

class BaseURLNode(template.Node):
    def __init__(self):
        pass
    def render(self, context):
        return get_script_prefix()

def do_base_url(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag does not requires an argument" % token.contents.split()[0])
    return BaseURLNode()

register.tag('base_url', do_base_url)
