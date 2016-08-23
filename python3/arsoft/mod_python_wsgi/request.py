from . import mod_python.apache

from base64 import b64decode
# WebOb
from webob import Request, Response
from webob.headers import ResponseHeaders

class ModPythonRequest(object):

    def __init__(self, environ):
        self.request = Request(environ, charset='utf8')
        self.response = Response()
        self.cleanup = self.cleanupData = None
        self._error_headers = ResponseHeaders()

    def add_common_vars(self):
        raise NotImplementedError()

    def add_handler(self):
        raise NotImplementedError()

    def allow_methods(self):
        raise NotImplementedError()

    @property
    def content_length(self):
        return self.response.content_length

    @content_length.setter
    def content_length(self, value):
        self.response.content_length = value

    @property
    def content_type(self):
        return self.response.content_type

    @content_type.setter
    def content_type(self, value):
        self.response.content_type = value

    def document_root(self):
        raise NotImplementedError()

    def get_basic_auth_pw(self):
        auth = self.request.authorization
        if auth:
            mechanism, token = auth
            username, password = b64decode(token).split(':', 1)
            self.user = username
            if mechanism == 'Basic':
                return password

    def get_config(self):
        raise NotImplementedError()

    def get_remote_host(self, type=None, str_is_ip=None):
        return self.request.remote_addr

    def get_options(self):
        raise NotImplementedError()

    @property
    def headers_in(self):
        return self.request.headers

    @property
    def headers_out(self):
        return self.response.headers

    @property
    def err_headers_out(self):
        return self._error_headers

    def internal_redirect(self):
        raise NotImplementedError()

    def log_error(self, message, level=None):
        try:
            print(message, file=self.request.environ['wsgi.errors'])
        except KeyError:
            raise NotImplementedError()

    def requires(self):
        raise NotImplementedError()

    def read(self, len_=-1):
        return self.request.body.read(len_)

    def readline(self, len_=-1):
        return self.request.body.readline(len_)

    def readlines(self, sizehint=-1):
        raise NotImplementedError()

    def register_cleanup(self, callable_, data=None):
        self.cleanup = callable_
        self.cleanupData = data

    def sendfile(self, path, offset=0, len_=-1):
        try:
            with open(path, 'r') as fh:
                fh.seek(offset)
                if len_ > -1:
                    self.response.body = fh.read(len_)
                else:
                    self.response.body = fh.read()
        except IOError:
            self.response.status = "404 Not Found"

    def send_http_header(self):
        pass

    @property
    def subprocess_env(self):
        return self.request.environ

    @property
    def uri(self):
        return self.request.path

    @property
    def user(self):
        return self.request.remote_user

    @user.setter
    def user(self, username):
        self.request.remote_user = username

    @user.deleter
    def user(self):
        self.request.remote_user = None

    def write(self, string, flush=1):
        self.response.body_file.write(string)

    def flush(self):
        pass

    def set_content_length(self, len_):
        self.response.content_length = len_
