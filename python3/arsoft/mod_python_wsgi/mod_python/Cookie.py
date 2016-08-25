#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

class CookieError(Exception):
    pass

class metaCookie(type):

    def __new__(cls, clsname, bases, clsdict):

        _valid_attr = (
            "version", "path", "domain", "secure",
            "comment", "max_age",
            # RFC 2965
            "commentURL", "discard", "port",
            # Microsoft Extension
            "httponly" )

        # _valid_attr + property values
        # (note __slots__ is a new Python feature, it
        # prevents any other attribute from being set)
        __slots__ = _valid_attr + ("name", "value", "_value",
                                   "_expires", "__data__")

        clsdict["_valid_attr"] = _valid_attr
        clsdict["__slots__"] = __slots__

        def set_expires(self, value):

            if type(value) == type(""):
                # if it's a string, it should be
                # valid format as per Netscape spec
                try:
                    t = time.strptime(value, "%a, %d-%b-%Y %H:%M:%S GMT")
                except ValueError:
                    raise ValueError("Invalid expires time: %s" % value)
                t = time.mktime(t)
            else:
                # otherwise assume it's a number
                # representing time as from time.time()
                t = value
                value = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT",
                                      time.gmtime(t))

            self._expires = "%s" % value

        def get_expires(self):
            return self._expires

        clsdict["expires"] = property(fget=get_expires, fset=set_expires)

        return type.__new__(cls, clsname, bases, clsdict)

# metaclass= workaround, see
# http://mikewatkins.ca/2008/11/29/python-2-and-3-metaclasses/#using-the-metaclass-in-python-2-x-and-3-x
_metaCookie = metaCookie('Cookie', (object, ), {})

class Cookie(_metaCookie):
    """
    This class implements the basic Cookie functionality. Note that
    unlike the Python Standard Library Cookie class, this class represents
    a single cookie (not a list of Morsels).
    """

    DOWNGRADE = 0
    IGNORE = 1
    EXCEPTION = 3

    def parse(Class, str, **kw):
        """
        Parse a Cookie or Set-Cookie header value, and return
        a dict of Cookies. Note: the string should NOT include the
        header name, only the value.
        """

        dict = _parse_cookie(str, Class, **kw)
        return dict

    parse = classmethod(parse)

    def __init__(self, name, value, **kw):

        """
        This constructor takes at least a name and value as the
        arguments, as well as optionally any of allowed cookie attributes
        as defined in the existing cookie standards.
        """
        self.name, self.value = name, value

        for k in kw:
            setattr(self, k.lower(), kw[k])

        # subclasses can use this for internal stuff
        self.__data__ = {}


    def __str__(self):

        """
        Provides the string representation of the Cookie suitable for
        sending to the browser. Note that the actual header name will
        not be part of the string.

        This method makes no attempt to automatically double-quote
        strings that contain special characters, even though the RFC's
        dictate this. This is because doing so seems to confuse most
        browsers out there.
        """

        result = ["%s=%s" % (self.name, self.value)]
        for name in self._valid_attr:
            if hasattr(self, name):
                if name in ("secure", "discard", "httponly"):
                    result.append(name)
                else:
                    result.append("%s=%s" % (name, getattr(self, name)))
        return "; ".join(result)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__,
                                str(self))


def get_cookies(req, cls=Cookie):
    cookie_dict = req.request.cookies
    cookie_dict.has_key = cookie_dict.__contains__
    return cookie_dict
