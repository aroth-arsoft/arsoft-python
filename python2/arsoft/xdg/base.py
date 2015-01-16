#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.inifile import IniFile
from arsoft.xmlfile import XmlFile
import re
import os.path
import tempfile

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
    def __init__(self, filename=None, company=None, product=None, name=None, ext=None):
        object.__setattr__(self, '_filename', filename)
        object.__setattr__(self, '_company', company)
        object.__setattr__(self, '_product', product)
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_ext', ext)
        if filename is not None:
            self._get_info_from_filename(filename)
        
    def _get_info_from_filename(self, filename):
        company = None
        product = None
        name = None
        ext = None
        if filename is not None:
            basename = os.path.basename(filename)
            (bname, ext) = os.path.splitext(basename)
            if '-' in basename:
                (company, rest) = basename.split('-')
                if '-' in rest:
                    (product, name) = basename.split('-')
                else:
                    name = rest
        object.__setattr__(self, '_company', company)
        object.__setattr__(self, '_product', product)
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_ext', ext)

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
        ret = ''
        if self._company is not None:
            if len(ret) > 0:
                ret = ret + '-' + self._company
            else:
                ret = self._company
        if self._product is not None:
            if len(ret) > 0:
                ret = ret + '-' + self._product
            else:
                ret = self._product
        if self._name is not None:
            if len(ret) > 0:
                ret = ret + '-' + self._name
            else:
                ret = self._name
        if self._ext is not None:
            ret = ret + self._ext
        return ret

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


    def __init__(self, filename=None, company=None, product=None, name=None, ext=None, maingroup=None):
        super(xdg_desktop_file, self).__init__(filename, company, product, name, ext)
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
 

class xdg_menu_file(xdg_file):
    def __init__(self, filename=None, company=None, product=None, name=None):
        print('xdg_menu_file')
        super(xdg_menu_file, self).__init__(filename, company, product, name, ext='.menu')
        self._xmlfile = XmlFile(filename, document_tag='Menu')
        self._root = None

    def open(self, filename=None):
        return self._xmlfile.open(filename)

    def save(self, filename=None):
        return self._xmlfile.save(filename)
    
    class menu_level(object):
        def __init__(self, xmlfile, xmlentity):
            self._xmlfile = xmlfile
            self._xmlentity = xmlentity
            self._childs = None
            self._name = None
            self._directory = None
            self._includes = None

        @property
        def childs(self):
            if self._childs is None:
                self._childs = []
                child_menus = XmlFile.getChildElementsByTagName(self._xmlentity, 'Menu')
                if child_menus:
                    for m in iter(child_menus):
                        child = xdg_menu_file.menu_level(self._xmlfile, m)
                        self._childs.append(child)
            return self._childs

        @property
        def includes(self):
            if self._includes is None:
                self._includes = []
                include_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Include')
                if include_items and len(include_items) > 0:
                    filename_items = XmlFile.getChildElementsByTagName(include_items[0], 'Filename')
                    for f in filename_items:
                        include_file = XmlFile.getNodeText(f)
                        self._includes.append(include_file)
            return self._includes
        @includes.setter
        def includes(self, value):
            self._includes = value
            
            new_include = self._xmlfile.doc.createElement('Include')
            for v in value:
                new_filename = self._xmlfile.doc.createElement('Filename')
                new_filename.appendChild(self._xmlfile.doc.createTextNode(v))
                new_include.appendChild(new_filename)
            include_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Include')
            if include_items and len(include_items) > 0:
                self._xmlentity.replaceChild(include_items[0], new_include)
            else:
                self._xmlentity.appendChild(new_include)
        
        @property
        def name(self):
            if self._name is None:
                name_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Name')
                if name_items and len(name_items) > 0:
                    self._name = XmlFile.getNodeText(name_items[0])
                else:
                    self._name = ''
            return self._name
        
        @name.setter
        def name(self, value):
            self._name = value
            name_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Name')
            if name_items and len(name_items) > 0:
                XmlFile.setNodeText(name_items[0], self._name)
            else:
                new_menu_item_name = self._xmlfile.doc.createElement('Name')
                new_menu_item_name.appendChild(self._xmlfile.doc.createTextNode(self._name))
                self._xmlentity.appendChild(new_menu_item_name)

        @property
        def directory(self):
            if self._directory is None:
                dir_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Directory')
                if dir_items and len(dir_items) > 0:
                    self._directory = XmlFile.getNodeText(dir_items[0])
                else:
                    self._directory = ''
            return self._directory

        @directory.setter
        def directory(self, value):
            self._directory = value
            dir_items = XmlFile.getChildElementsByTagName(self._xmlentity, 'Directory')
            if dir_items and len(dir_items) > 0:
                XmlFile.setNodeText(dir_items[0], self._directory)
            else:
                new_menu_item_directory = self._xmlfile.doc.createElement('Directory')
                new_menu_item_directory.appendChild(self._xmlfile.doc.createTextNode(self._directory))
                self._xmlentity.appendChild(new_menu_item_directory)
        
        def __repr__(self):
            return self.dump()

        def dump(self, depth=0):
            ret = ('    ' * depth) + self.name + '(' + self.directory + ')\n'
            for i in self.includes:
                ret = ret + ('    ' * depth) + '->' + i + '\n'
            for c in self.childs:
                ret = ret + c.dump(depth + 1)
            return ret
        
        def add_child(self, name, directory=None, includes=[]):
            # ensure childs are loaded
            dummy_childs = self.childs
            
            # create the new XML entity
            new_menu_item = self._xmlfile.doc.createElement('Menu')
            new_menu_item_name = self._xmlfile.doc.createElement('Name')
            new_menu_item_name.appendChild(self._xmlfile.doc.createTextNode(name))
            new_menu_item.appendChild(new_menu_item_name)
            if directory:
                new_menu_item_directory = self._xmlfile.doc.createElement('Directory')
                new_menu_item_directory.appendChild(self._xmlfile.doc.createTextNode(directory))
                new_menu_item.appendChild(new_menu_item_directory)
            if len(includes) > 0:
                new_menu_item_include = self._xmlfile.doc.createElement('Include')
                for i in includes:
                    i_filename = self._xmlfile.doc.createElement('Filename')
                    i_filename.appendChild(self._xmlfile.doc.createTextNode(i))
                    new_menu_item_include.appendChild(i_filename)
                new_menu_item.appendChild(new_menu_item_include)
            self._xmlentity.appendChild(new_menu_item)
            new_item = xdg_menu_file.menu_level(self._xmlfile, new_menu_item)
            self._childs.append(new_item)

    @property
    def root(self):
        if self._root is None:
            self._root = xdg_menu_file.menu_level(self._xmlfile, xmlentity=self._xmlfile.root)
        return self._root

