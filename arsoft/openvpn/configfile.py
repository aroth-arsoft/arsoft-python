""" This is a parser for openvpn config files, version 3.

"""

from arsoft.inifile import *
import sys

class ConfigFile:
    def __init__(self, filename):
        self.filename = filename
        self._conf = None

    def _parse_file(self):
        self._conf  = IniFile(commentPrefix='#', keyValueSeperator=' ', disabled_values=False)
        if not self._conf .open(self.filename):
            self._conf = None
        else:
            self._conf.get(section=None, key='server', default=None)

    @property
    def status_version(self):
        if self._conf is not None:
            ret = int(self._conf.get(section=None, key='status-version', default=-1))
        else:
            ret = None
        return ret

    @property
    def status_file(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            fe = f.split(' ')
            ret = fe[0]
        else:
            ret = None
        return ret

    @property
    def status_interval(self):
        if self._conf is not None:
            f = self._conf.get(section=None, key='status', default=None)
            fe = f.split(' ')
            if len(fe) > 1:
                ret = int(fe[1])
            else:
                ret = -1
        else:
            ret = None
        return ret

if __name__ == '__main__':
    files = sys.argv[1:]

    for file in files:
        f = ConfigFile(file)
