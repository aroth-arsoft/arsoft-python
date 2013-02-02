#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from django import template
from django.core.urlresolvers import get_script_prefix
from django.conf import settings

register = template.Library()

class MediaURLNode(template.Node):
    def __init__(self, url):
        self._url = get_script_prefix()
        while self._url.endswith('/'):
            self._url = self._url[:-1]
        try:
            settings_media_url = getattr(settings,'MEDIA_URL')
            self._url = self._url + settings_media_url
        except AttributeError as e:
            pass
        if url:
            self._url = self._url + url

    def render(self, context):
        return self._url

def do_media_url(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, url = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    if not (url[0] == url[-1] and url[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    return MediaURLNode(url[1:-1])

register.tag('media_url', do_media_url)
