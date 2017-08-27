#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport
# and https://github.com/Coi-l/EurosportPlayer.bundle/blob/master/Contents/Services/Shared%20Code/eurosportplayer.pys

import json

BASE_LOGIN_PATH = "https://playercrm.ssl.eurosport.com/JsonPlayerCrmApi.svc/Login?"
BASE_UNLINK_PATH = "https://playercrm.ssl.eurosport.com/JsonPlayerCrmApi.svc/Unlink?"
#BASE_PROGRAMS_PATH = "http://videoshop.ext.eurosport.com/JsonProductService.svc/GetAllProductsByDeviceMobile?"
BASE_PROGRAMS_PATH = "https://videoshop-partners.eurosportplayer.com/JsonProductService.svc/GetAllChannelsCache?"

BASE_URL = 'http://www.eurosportplayer.com'
BASE_GLOBAL_API = 'https://global-api.svcs.eurosportplayer.com/'
BASE_SEARCH_API = 'https://search-api.svcs.eurosportplayer.com/'

time_format = '%Y-%m-%dT%H:%M:%SZ'
date_format = '%Y-%m-%d'


DEFAULT_LOGIN_PARAMETERS = {
    "c": "EUR",
    "d": 4,
    "s": 1,
    "v": "2.2.2",
    "p": "1",
    "b": "google",
    "ap": 21,
    "mi": "LRX22G",
    "mn": "Nexus 7",
    "ma": "LGE",
    "tt": "Phone",
    "di": "dimension=1196x768,density=319,79x318,74,scale=2,00x2,00",
    "o": "11",
    "osn": "Android",
    "osv": "5.0.1",
    "g": "GB",
    "l": "gb",
    "st": "2"
}

def log(msg):
    print(msg)

class Constants(object):

    #Convert locale id to isolanguagecode
    l2c = {"en":0, "de":1, "en-gb":2, "fr":3, "it":4, "nl":5, "es":6, "se":7, "dk":11, "fi":12, "no":13, "pl":14, "ru":15}
    # only list the special cases; all other language simply use the uppercase language code
    l2g = {"en":'GB',"en-gb":'GB'}

    @staticmethod
    def get_locale_id(language_code):
        if language_code is None:
            return 0
        code = language_code.lower()
        if code in Constants.l2c:
            return Constants.l2c[code]
        else:
            return 0

    @staticmethod
    def get_geoloc_id(language_code):
        if language_code is None:
            return 'GB'
        code = language_code.lower()
        if len(code) == 0:
            return 'GB'
        elif code in Constants.l2g:
            return Constants.l2g[code]
        else:
            return language_code.upper()


def prepare_application_context():
    return json.dumps(DEFAULT_LOGIN_PARAMETERS)



