#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile

class Config(object):

    def __init__(self, filename=None, email=None, password=None, quality=None, geo=None, language=None, country=None, devtype=None, productid=None):
        self.email = email
        self.password = password
        self.quality = quality
        self.geo = geo
        self.language = language
        self.country = country
        self.devtype = devtype
        self.productid = productid
        if filename is not None:
            self.open(filename)

    def open(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.open(filename)

        self.email = inifile.get(None, 'EMail', '')
        self.password = inifile.get(None, 'Password', '')
        self.quality = inifile.get(None, 'VideoQuality', None)
        self.geo = inifile.get(None, 'Geo', None)
        self.language = inifile.get(None, 'Language', None)
        self.country = inifile.get(None, 'Country', None)
        self.devtype = inifile.getAsInteger(None, 'DeviceType', None)
        self.productid = inifile.getAsInteger(None, 'ProductId', None)
        return True

    def save(self, filename):
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.open(filename)

        inifile.set(None, 'EMail', self.email)
        inifile.set(None, 'Password', self.password)
        inifile.set(None, 'VideoQuality', self.quality)
        inifile.set(None, 'Geo', self.geo)
        inifile.set(None, 'Language', self.language)
        inifile.set(None, 'Country', self.country)
        inifile.setAsInteger(None, 'DeviceType', self.devtype)
        inifile.setAsInteger(None, 'ProductId', self.productid)
        return inifile.save(filename)

    def __str__(self):
        ret = ''
        ret = ret + 'email=' + str(self.email) + ','
        ret = ret + 'password=' + str(self.password) + ','
        ret = ret + 'quality=' + str(self.quality) + ','
        ret = ret + 'geo=' + str(self.geo) + ','
        ret = ret + 'language=' + str(self.language) + ','
        ret = ret + 'country=' + str(self.country) + ','
        ret = ret + 'devtype=' + str(self.devtype) + ','
        ret = ret + 'productid=' + str(self.productid)
        return ret


