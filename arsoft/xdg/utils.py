#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile
from arsoft.utils import runcmd
import re
import os.path

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
    def __init__(self, filename=None, company=None, product=None, name=None):
        object.__setattr__(self, '_filename', filename)
        object.__setattr__(self, '_company', company)
        object.__setattr__(self, '_product', product)
        object.__setattr__(self, '_name', name)
        if filename is not None:
            self._get_info_from_filename(filename)
        
    def _get_info_from_filename(self, filename):
        company = None
        product = None
        name = None
        if filename is not None:
            basename = os.path.basename(filename)
            if '-' in basename:
                (company, rest) = basename.split('-')
                if '-' in rest:
                    (product, name) = basename.split('-')
                else:
                    name = rest
        object.__setattr__(self, '_company', company)
        object.__setattr__(self, '_product', product)
        object.__setattr__(self, '_name', name)

    @property
    def company(self):
        return self._company
    @property
    def product(self):
        return self._product
    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        return self._filename

    @property
    def suggested_basename(self):
        if self._product is not None:
            return self._company + '-' + self._product + '-' + self._name + '.desktop'
        else:
            return self._company + '-' + self._name + '.desktop'

class xdg_desktop_file(xdg_file):
    
    MAIN_CATEGORIES = ["AudioVideo", "Audio", "Video", "Development", "Education", "Game", "Graphics", "Network", "Office", "Science", "Settings", "System", "Utility"]
    ADDITIONAL_CATEGORIES = ['Building', 'Debugger', 'IDE', 'GUIDesigner', 'Profiling', 'RevisionControl', 'Translation', 'Calendar', 
                                'ContactManagement', 'Database', 'Dictionary', 'Chart', 'Email', 'Finance', 'FlowChart', 'PDA', 
                                'ProjectManagement', 'Presentation', 'Spreadsheet', 'WordProcessor', '2DGraphics', 'VectorGraphics', 'RasterGraphics', 
                                '3DGraphics', 'Scanning', 'OCR', 'Photography', 'Publishing', 'Viewer', 'TextTools', 'DesktopSettings', 'HardwareSettings', 
                                'Printing', 'PackageManager', 'Dialup', 'InstantMessaging', 'Chat', 'IRCClient', 'Feed', 'FileTransfer', 'HamRadio', 'News', 
                                'P2P', 'RemoteAccess', 'Telephony', 'TelephonyTools', 'VideoConference', 'WebBrowser', 'WebDevelopment', 'Midi', 'Mixer', 
                                'Sequencer', 'Tuner', 'TV', 'AudioVideoEditing', 'Player', 'Recorder', 'DiscBurning', 'ActionGame', 'AdventureGame', 
                                'ArcadeGame', 'BoardGame', 'BlocksGame', 'CardGame', 'KidsGame', 'LogicGame', 
                                'RolePlaying', 'Shooter', 'Simulation', 'SportsGame', 'StrategyGame', 
                                'Art', 'Construction', 'Music', 'Languages', 'ArtificialIntelligence', 'Astronomy', 'Biology', 'Chemistry', 
                                'ComputerScience', 'DataVisualization', 'Economy', 'Electricity', 'Geography', 'Geology', 'Geoscience', 
                                'History', 'Humanities', 'ImageProcessing', 'Literature', 'Maps', 'Math', 'NumericalAnalysis', 
                                'MedicalSoftware', 'Physics', 'Robotics', 'Spirituality', 'Sports', 'ParallelComputing', 'Amusement', 'Archiving', 
                                'Compression', 'Electronics', 'Emulator', 'Engineering', 'FileTools', 'FileManager', 'TerminalEmulator', 'Filesystem', 
                                'Monitor', 'Security', 'Accessibility', 'Calculator', 'Clock', 'TextEditor', 'Documentation', 'Adult', 'Core', 
                                'KDE', 'GNOME', 'XFCE', 'GTK', 'Qt', 'Motif', 'Java', 'ConsoleOnly']

    PROPERTY_TYPE_DICT = { 'Categories':'categories', 
                            'Version':'number',
                            'Keywords':'list/string'
                            }

    
    def __init__(self, filename=None, company=None, product=None, name=None, maingroup=None):
        super(xdg_desktop_file, self).__init__(filename, company, product, name)
        super(xdg_desktop_file, self).__setattr__('_maingroup', maingroup)
        super(xdg_desktop_file, self).__setattr__('_inifile', IniFile(filename, commentPrefix=';', keyValueSeperator='=', disabled_values=False))

    @staticmethod
    def _check_boolean(value):
        # 1 or 0 : deprecated but ok
        if (value == "1" or value == "0"):
            return True
        # true or false: ok
        elif (value == "true" or value == "false"):
            return True
        else:
            return False

    @staticmethod
    def _check_number(value):
        # float() ValueError
        try:
            float(value)
            return True
        except:
            return False

    @staticmethod
    def _check_integer(value):
        # int() ValueError
        try:
            int(value)
            return True
        except:
            return False

    @staticmethod
    def _check_point(value):
        if not re.match("^[0-9]+,[0-9]+$", value):
            return False
        else:
            return True

    @staticmethod
    def _check_string(value):
        return True if is_ascii(value) else False

    @staticmethod
    def _check_localestring(value):
        return True if is_utf8(value) else False

    @staticmethod
    def _check_regex(value):
        try:
            re.compile(value)
            return True
        except:
            return False

    @staticmethod
    def _check_list(value):
        return True if isinstance(value, list) else False

    @staticmethod
    def _check_list_of(value, type):
        if isinstance(value, list):
            for v in value:
                if not xdg_desktop_file._check_value(v, type):
                    return False
            return True
        else:
            return False

    @staticmethod
    def _check_categories(value):
        if xdg_desktop_file._check_list_of(value, 'string'):
            for v in value:
                if not v in xdg_desktop_file.MAIN_CATEGORIES and not v in xdg_desktop_file.ADDITIONAL_CATEGORIES:
                    return False
            return True
        else:
            return False

    @staticmethod
    def _check_value(value, type):
        if type is None:
            ret = True
        else:
            if '/' in type:
                (maintype, subtype) = type.split('/')
            else:
                maintype = type
                subtype = None
            if maintype == "string":
                ret = xdg_desktop_file._check_string(value)
            elif maintype == "localestring":
                ret = xdg_desktop_file._check_localestring(value)
            elif maintype == "boolean":
                ret = xdg_desktop_file._check_boolean(value)
            elif maintype == "numeric":
                ret = xdg_desktop_file._check_number(value)
            elif maintype == "integer":
                ret = xdg_desktop_file._check_integer(value)
            elif maintype == "regex":
                ret = xdg_desktop_file._check_regex(value)
            elif maintype == "point":
                ret = xdg_desktop_file._check_point(value)
            elif maintype == "list":
                if subtype is None:
                    ret = xdg_desktop_file._check_list(value)
                else:
                    ret = xdg_desktop_file._check_list_of(value, subtype)
            elif maintype == "categories":
                ret = xdg_desktop_file._check_categories(value)
            else:
                # unknown type, assume user knows what he's doing.
                ret = True
        return ret
    
    @staticmethod
    def _get_type_for_property(propname, fallback_type=None):
        if propname in xdg_desktop_file.PROPERTY_TYPE_DICT:
            return xdg_desktop_file.PROPERTY_TYPE_DICT[propname]
        else:
            return fallback_type

    def set(self, name, value, type=None):
        if type is None:
            type = xdg_desktop_file._get_type_for_property(name)
        if not self._check_value(value, type):
            raise AttributeError('property %s of type %s has invalid value %s' %(name, type, value))
        else:
            if isinstance(value, list):
                value_str = ';'.join(value)
            else:
                value_str = str(value)
            self._inifile.set(self._maingroup, name, value_str)

    def get(self, name, type=None):
        if type is None:
            type = xdg_desktop_file._get_type_for_property(name)
        if type:
            if '/' in type:
                (maintype, subtype) = type.split('/')
            else:
                maintype = type
                subtype = None
        else:
            maintype = None
        value = self._inifile.get(self._maingroup, name, None)
        if maintype == 'categories' or maintype == 'list':
            value = value.split(';')
        if not self._check_value(value, type):
            raise AttributeError('property %s of type %s has invalid value %s' %(name, type, value))
        else:
            return value

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self.set(name, value, None)

    def open(self, filename=None):
        return self._inifile.open(filename)

    def save(self, filename=None):
        return self._inifile.save(filename)

class desktop_entry(xdg_desktop_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(desktop_entry, self).__init__(filename=filename, company=company, product=product, name=name, maingroup='Desktop Entry')
        if filename is None:
            self.Version = '1.0'
            self.Encoding = 'UTF-8'

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
            if runcmd('xdg-desktop-menu', args) == 0:
                ret = True
            else:
                ret = False
        os.remove(tmpfile)
        os.rmdir(tmppath)
        return ret
        
class icon_file(xdg_file):
    
    def __init__(self, filename=None, company=None, product=None, name=None):
        super(icon_file, self).__init__(filename=filename, company=company, product=product, name=name)
    
    def install(self):
        tmppath = tempfile.mkdtemp()
        tmpfile = os.path.join(tmppath, self.suggested_basename)
        
        fullname = os.path.join(self._terra3d_icon_dir, filename)
        if name is None:
            name = os.path.basename(filename)
            (basename, ext) = os.path.splitext(name)
            name = 'fast-' + basename
        
        args = ['install', '--size', '32', fullname, name]
        if runcmd('xdg-icon-resource', args) == 0:
            ret = True
        else:
            ret = False
        return ret
 

if __name__ == '__main__':
    de = desktop_entry(company='arsoft', product='test', name='editor')
    print de.company
    print de.product
    print de.name
    de.Version = '1.0'
    de.Categories = ['Utility', 'KDE']
    de.Keywords = ['Bar', 'Foo']
    de.save('test.desktop')
    
    de2 = desktop_entry('test.desktop')
    print de2.Version
    print de2.Categories
    print de2.Keywords
