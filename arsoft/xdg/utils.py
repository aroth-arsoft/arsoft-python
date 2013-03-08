#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile

def is_ascii(s):
    """Return True if a string consists entirely of ASCII characters."""
    try:
        s.encode('ascii', 'strict')
        return True
    except UnicodeError:
        return False

def is_utf8(s):
    """Return True if a string consists entirely of ASCII characters."""
    try:
        s.encode('utf-8', 'strict')
        return True
    except UnicodeError:
        return False

class xdg_file(object):
    def __init__(self, filename, maingroup):
        self._inifile = IniFile(filename, commentPrefix=';', keyValueSeperator='=', disabled_values=False)
        self._maingroup = maingroup
        self._get_info_from_filename(filename)
        
    def _get_info_from_filename(self, filename):
        self._company = None
        self._product = None
        self._name = None
        basename = os.path.basename(filename)
        if '-' in basename:
            (self._company, rest) = basename.split('-')
            if '-' in rest:
                (self._product, self._name) = basename.split('-')
            else:
                self._name = rest

    @staticmethod
    def _check_boolean(self, value):
        # 1 or 0 : deprecated but ok
        if (value == "1" or value == "0"):
            return True
        # true or false: ok
        elif (value == "true" or value == "false"):
            return True
        else:
            return False

    @staticmethod
    def _check_number(self, value):
        # float() ValueError
        try:
            float(value)
            return True
        except:
            return False

    @staticmethod
    def _check_integer(self, value):
        # int() ValueError
        try:
            int(value)
            return True
        except:
            return False

    @staticmethod
    def _check_point(self, value):
        if not re.match("^[0-9]+,[0-9]+$", value):
            return False
        else:
            return True

    @staticmethod
    def _check_string(self, value):
        return True if is_ascii(value) else False

    @staticmethod
    def _check_localestring(self, value):
        return True if is_utf8(value) else False

    @staticmethod
    def _check_regex(self, value):
        try:
            re.compile(value)
            return True
        except:
            return False

    @staticmethod
    def _check_value(value, type):
        if type is None:
            ret = True
        elif type == "string":
            ret = xdg_file._check_string(value)
        elif type == "localestring":
            ret = xdg_file._check_localestring(value)
        elif type == "boolean":
            ret = xdg_file._checkBoolean(value)
        elif type == "numeric":
            ret = xdg_file._checkNumber(value)
        elif type == "integer":
            ret = xdg_file._checkInteger(value)
        elif type == "regex":
            ret = xdg_file._checkRegex(value)
        elif type == "point":
            ret = xdg_file._checkPoint(value)
        else:
            # unknown type, assume user knows what he's doing.
            ret = True
        return ret

    def set(self, name, value, type=None):
        if not self._check_value(value, type):
            raise AttributeError(name)
        else:
            if isinstance(value, list):
                value_str = ';'.join(value)
            else:
                value_str = str(value)
            self._inifile.set(self._maingroup, name, value_str)

    def get(self, name, type=None):
        value = self._inifile.get(self._maingroup, name, None)
        if not self._check_value(value, type):
            raise AttributeError(name)
        else:
            if type == 'string':
                value = value.split(';')
            return value

    def __getattr__(self, name):
        self.get(name, None)

    def __setattr__(self, name, value):
        self.set(name, value, None)

    def open(self, filename=None):
        return self._inifile.open(filename)

    def save(self, filename=None):
        return self._inifile.save(filename)

    @property
    def filename(self):
        return self._inifile.filename

    @property
    def suggested_basename(self):
        if self._product is not None:
            return self._company + '-' + self._product + '-' + self._name + '.desktop'
        else:
            return self._company + '-' + self._name + '.desktop'


class desktop_file(xdg_file):
    def __init__(self, filename):
        super(desktop_file, self).__init__(filename, 'Desktop Entry')

    def _xdg_desktop_file(self, name, exe, params=[], description='', icon=None, categories=[], startupNotify=True):
        
        desktop_file_name = name.replace(' ', '').replace('-', '').lower()
        try:
            fpath = tempfile.mkdtemp()
            desktop_file = os.path.join(fpath, 'fast-' + desktop_file_name + '.desktop')
            f = open(desktop_file, "w")
            f.write('[Desktop Entry]\n')
            f.write('Version=1.0\n')
            f.write('Encoding=UTF-8\n')
            f.write('Name=' + name + '\n')
            f.write('GenericName=' + description + '\n')
            f.write('Type=Application\n')
            f.write('Categories=' + ';'.join(categories) + ';\n')
            f.write('Terminal=false\n')
            if startupNotify:
                f.write('StartupNotify=true\n')
            else:
                f.write('StartupNotify=false\n')

            if params is not None and len(params) > 0:
                execline = '"' + exe + '" ' + ' '.join(params)
            else:
                execline = '"' + exe + '"'
            f.write('Exec=' + execline + '\n')
            if icon:
                f.write('Icon=' + icon + '\n')
            f.close()
            ret = True
        except IOError:
            ret = False
        
        if ret:
            args = ['install', desktop_file]
            if self._runcmd('xdg-desktop-menu', args) == 0:
                ret = True
            else:
                ret = False
            os.remove(desktop_file)
            os.rmdir(fpath)
        return ret
    
    def install(self):
        tmppath = tempfile.mkdtemp()
        tmpfile = os.path.join(tmppath, self.suggested_basename)
        ret = self.save(tmpfile)
        if ret:
            args = ['install', tmpfile]
            if self._runcmd('xdg-desktop-menu', args) == 0:
                ret = True
            else:
                ret = False
        os.remove(tmpfile)
        os.rmdir(tmppath)
        return ret
        
    
    def _xdg_icon_file(self, filename, name=None):
        
        fullname = os.path.join(self._terra3d_icon_dir, filename)
        if name is None:
            name = os.path.basename(filename)
            (basename, ext) = os.path.splitext(name)
            name = 'fast-' + basename
        
        args = ['install', '--size', '32', fullname, name]
        if self._runcmd('xdg-icon-resource', args) == 0:
            ret = True
        else:
            ret = False
        return ret
 
