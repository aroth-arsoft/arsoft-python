#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import xmlrpc.client
import sys
from urllib.parse import urlparse, urljoin

class TracXmlrpc(object):
    def __init__(self, url=None, server=None, base='/', username=None, password=None, https=True):
        if url is not None:
            o = urlparse(url)
            if o.username is None and username is not None:
                o.username = username
                if o.password is None and password is not None:
                    o.password = password
        else:
            uri = 'https://' if self._https else 'http://'
            if username:
                uri = uri + username
                if password:
                    uri = uri + ':' + password
                uri = uri + '@'
            uri = uri + server
            uri = uri + base
            o = urlparse(uri)

        self._url = o.geturl()
        print((self._url))

        self._server = server
        self._base = base
        self._username = username
        self._password = password
        self._https = https
        self._cxn = None
        
        self._connect()
        
    def _connect(self):
        url = self._url + '/login/xmlrpc'
        print(url)
        self._cxn = xmlrpc.client.ServerProxy(url)
        return True if self._cxn is not None else False
        
    @property
    def api_version(self):
        return self._cxn.system.getAPIVersion()
    
    @property
    def methods(self):
        return self._cxn.system.listMethods()
    
    def method_help(self, method):
        return self._cxn.system.methodHelp(method)

if __name__ == '__main__':
    t = TracXmlrpc(url=sys.argv[1])
    print((t.api_version))
    print((t.methods))
 
