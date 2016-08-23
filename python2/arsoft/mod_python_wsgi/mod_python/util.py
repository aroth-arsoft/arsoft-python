
from cgi import parse_qs as cgi_parse_qs, parse_qsl as cgi_parse_qsl


class Field(object):

    def __init__(self, name, value):
        self.name = name
        self.file = value

    def __del__(self):
        self.file.close()

    def __getattr__(self, name):
        if name != 'value':
            raise AttributeError(name)
        elif self.file:
            self.file.seek(0)
            value = self.file.read()
            self.file.seek(0)

        return value


class StringField(str):

    def __init__(self, value):
        super(StringField, self).__init__(value)

    @property
    def value(self):
        return self

    @property
    def filename(self):
        return None


class FieldStorage(object):

    def __init__(self, req, keep_blank_values=False, strict_parsing=None):
        """Constructor.

        :arg req: The request object
        :type req: mod_python_wsgi.request.ModPythonRequest
        :arg keep_blank_values: blank values in URL encoded form data should
            be treated as blank strings
        :type keep_blank_values: bool

        """
        # Parse request parameters into a single data structure
        self._multidict = req.request.params
        self.list = [self._wrap(k, v) for k, v in self._multidict.iteritems()]

    def __getitem__(self, key):
        return self._wrap(key, self._multidict.__getitem__(key))

    def _wrap(self, name, value):
        if hasattr(value, 'read'):
            return Field(name, value)
        elif hasattr(value, 'file'):
            return Field(name, value.file)
        elif value is not None:
            if isinstance(value, unicode):
                f = StringField(value.encode('utf8'))
            else:
                f = StringField(value)
            f.name = name
            return f

    def get(self, key, default=None):
        return self._wrap(key, self._multidict.get(key, default))

    def getlist(self, key):
        return [self._wrap(key, v) for v in self._multidict.getall(key)]

    def getfirst(self, key, default=None):
        return self.get(key, default)

    def getvalue(self, key, default=None):
        val = self.getlist(key)
        if not val:
            return default
        elif len(val) == 1:
            return val[0]
        else:
            return val

    def has_key(self, key):
        return key in self._multidict


def parse_qs(*args):
    return cgi_parse_qs(*args)


def parse_qsl(*args):
    return cgi_parse_qsl(*args)


def redirect(req, location, permanent=0, text=None):
    req.response.location = location
    if permanent:
        req.response.status_code = 301
    else:
        req.response.status_code = 307
    if text:
        req.response.body = text
