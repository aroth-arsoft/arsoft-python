
class Cookie(object):
    pass


def get_cookies(req, cls=Cookie):
    cookie_dict = req.request.cookies
    cookie_dict.has_key = cookie_dict.__contains__
    return cookie_dict
