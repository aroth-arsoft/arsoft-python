"""WSGI Application to wrap a mod_python callable.

This is usually the `handler` function that would have been configured for
mod_python.
"""

import mod_python.apache
from request import ModPythonRequest


class ModPythonWSGIApp(object):

    def __init__(self, callable_):
        self.callable = callable_

    def __call__(self, environ, start_response):
        request = ModPythonRequest(environ)
        self.excecute_callable(request)
        return request.response(environ, start_response)

    def excecute_callable(self, request):
        try:
            try:
                retval = self.callable(request)
                if retval == 1:
                    # Request declined !?
                    request.response.status = "502 Bad Gateway"
                elif retval:
                    request.response.status_code = retval
                elif request.response.status is None:
                    # Status not set
                    # apache.OK
                    request.response.status = "200 OK"
            except mod_python.apache.SERVER_RETURN as ex:
                request.response.status_code = ex.status_code
            except Exception as ex:
                print('unknown ex %s %s' % (type(ex), str(ex)))
        finally:
            if request.cleanup is not None:
                request.cleanup(request.cleanupData)


class BasicAuthModPythonWSGIApp(ModPythonWSGIApp):

    def __init__(self, callable_, authcallable, realm="Protected"):
        super(BasicAuthModPythonWSGIApp, self).__init__(callable_)
        self.authcallable = authcallable
        self.realm = realm

    def __call__(self, environ, start_response):
        request = ModPythonRequest(environ)
        # Check authentication callable returns zero status
        authstatus = self.authcallable(request)
        if authstatus == 401:
            # Add WWW-Authenticate field
            request.response.status = "401 Unauthorized"
            request.response.headers['WWW-Authenticate'] = (
                'Basic realm="{0}"'.format(self.realm)
            )
        elif authstatus == apache.OK:
            self.excecute_callable(request)
        else:
            request.response.status_code = authstatus
        return request.response(environ, start_response)
