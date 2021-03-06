#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport
# and https://github.com/stschake/eurosportCapper/blob/master/eurosportCapper/Eurosport.cs

import urllib.request
import urllib.parse
from .Constants import *
import json


class Login:
    instance = None

    @staticmethod
    def configure(username, password, options={}):
        Login.instance = Login(username, password, options)

    @staticmethod
    def get_instance():
        if Login.instance is None:
            raise Login.IsNotConfigured
        return Login.instance

    __username = None
    __password = None
    __logged_in_successfully = False

    __confirmation_data = None

    def __init__(self, username, password, options={}):
        self.__username = username
        self.__password = password
        self.__options = options

    def prepare_application_context(self):

        context    = {'g':Constants.get_geoloc_id(self.__options.get('geoloc',None)),
                        'd':str(self.__options.get('devtype', 2)),
                        'l':str(Constants.get_locale_id(self.__options.get('language', None))),
                        'p':str(self.__options.get('productid', 9)),
                        'v':self.__options.get('version', '5.2.2'),
                        'c':self.__options.get('country', 'EUR'),
                        's':'1',
                        "li": 2,
                        'b':'7',
                        "mn":"iPad",
                        "tt":"Pad",
                        }
        return context

    def _prepare_login_data(self):
        return json.dumps({
            "email": self.__username,
            "password": self.__password,
            'udid':'00000000-0000-0000-0000-000000000000'
        })


    def _get_all_query_parameters(self):
        url = {
            "data": self._prepare_login_data(),
            "context": self.prepare_application_context()
        }
        if self.__options.get('debug', False):
            print('Login data: %s' % url['data']) 
            print('Login context: %s' % url['context'])
        return urllib.parse.urlencode(url)

    def do_login(self):
        login_url = BASE_LOGIN_PATH
        login_url += self._get_all_query_parameters()
        try:
            print('do_login %s' % login_url)
            raw_response = urllib.request.urlopen(login_url)
            if not raw_response:
                raise Login.NetworkError

            login_response = LoginResponse(raw_response)
            self.confirm(login_response.get_confirmation())
        except urllib.error.HTTPError as e:
            raise Login.HTTPError(e)

    def confirm(self, login_confirmation):
        if self.__options.get('debug', False):
            print('Login confirm: %s' % login_confirmation) 
        self.__logged_in_successfully = True
        self.__confirmation_data = login_confirmation

    def get_confirmation(self):
        if not self.__confirmation_data:
            self.do_login()
        return self.__confirmation_data

    class IsNotConfigured(Exception):
        pass

    class NetworkError(Exception):
        pass

    class HTTPError(NetworkError):
        def __init__(self, http_ex):
            self._http_ex = http_ex

    class LoginIncorrect(Exception):
        pass

    class NotYetProcessed(Exception):
        pass

    class InvalidLoginData(Exception):
        pass

    class IncorrectJson(Exception):
        pass

    class InvalidContext(Exception):
        pass


class LoginResponse:

    __response_body = None

    def __init__(self, response):
        self.__response_body = json.loads(response.read().decode('utf8'))
        self.process_response()

    def process_response(self):
        if not self.__response_body:
            raise Login.IncorrectJson
        if self.__response_body["Response"]["Success"] != 1:
            if self.__response_body["Response"]["Message"] == 'Invalid Context':
                raise Login.InvalidContext
            else:
                print(json.dumps(self.__response_body, indent='  '))
                raise Login.InvalidLoginData(self.__response_body["Response"]["Message"])

    def get_confirmation(self):
        if not self.__response_body:
            raise Login.NotYetProcessed
        return {
            "userid": self.__response_body["Id"],
            "hkey": self.__response_body["Hkey"],
            "languageid": 2,
            #"isfullaccess": 0,
            #"isbroadcasted": 0,
            #"epglight": False
        }

