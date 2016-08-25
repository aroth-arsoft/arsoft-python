#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;


class Cookie(object):
    pass


def get_cookies(req, cls=Cookie):
    cookie_dict = req.request.cookies
    cookie_dict.has_key = cookie_dict.__contains__
    return cookie_dict
