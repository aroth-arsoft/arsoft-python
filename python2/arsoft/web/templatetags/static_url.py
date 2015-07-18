#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from django import template
from django.core.urlresolvers import get_script_prefix
from django.conf import settings

register = template.Library()

class StaticURLNode(template.Node):
    def __init__(self, url):
        self._url = get_script_prefix()
        try:
            self._url = getattr(settings,'STATIC_URL')
        except AttributeError:
            pass
        if url:
            self._url = self._url + url

    def render(self, context):
        return self._url

def do_static_url(parser, token):
    url = None
    # split_contents() knows not to split quoted strings.
    e = token.split_contents()
    if len(e) >= 2:
        url = e[1]
    tag_name = e[0] if e else None
    if url:
        if not (url[0] == url[-1] and url[0] in ('"', "'")):
            raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
        url = url[1:-1]
    return StaticURLNode(url)

register.tag('static_url', do_static_url)
