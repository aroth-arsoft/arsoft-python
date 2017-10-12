#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re
import datetime
import os
from .timestamp import timestamp_from_datetime
from .utils import unquote_string, escape_string_for_c, unescape_string_from_c

class IniSection(object):

    def __init__(self, inifile, name, lineno=-1, original=None, comment=''):
        self.inifile = inifile
        self.name = name
        self.lineno = lineno
        self.original = original
        self.comment = comment
        self.values = []

    def clone(self, newinifile=None):
        ret = IniSection(newinifile if newinifile else self.inifile, self.name, self.lineno, self.original, self.comment)
        for v in iter(self.values):
            ret.values.append(v.clone(newinifile))
        return ret

    class IniLine(object):
        inifile = None
        lineno = -1
        original = ''
        key = ''
        value = ''
        comment = ''
        disabled = False
        def __init__(self, inifile, lineno, original, key, value, comment='', disabled=False):
            self.inifile = inifile
            self.lineno = lineno
            self.original = original
            self.key = key
            self.value = value
            self.comment = comment
            self.disabled = disabled

        def clone(self, newinifile=None):
            ret = IniSection.IniLine(newinifile if newinifile else self.inifile, self.lineno, self.original, self.key, self.value, self.comment, self.disabled)
            return ret

        def asString(self, only_data=False):
            if self.original is not None and not only_data:
                ret = self.original
            else:
                if self.disabled == False:
                    ret = ''
                else:
                    ret = self.inifile.m_commentPrefix
                if self.key is not None:
                    ret += self.key + self.inifile.m_keyValueSeperator
                    if self.value is not None:
                        ret += str(self.value)
                if self.comment is not None and not only_data:
                    if len(ret) > 0:
                        ret += ' ' + self.inifile.m_commentPrefix + self.comment
                    else:
                        ret += self.inifile.m_commentPrefix + self.comment
            if only_data:
                if len(ret) > 0:
                    ret += '\n'
            else:
                ret += '\n'
            return ret

        def __str__(self):
            return self.asString(only_data=False)

        def __repr__(self):
            return self.asString(only_data=False)

    def get(self, key, default=''):
        for v in self.values:
            if v.key == key:
                return v.value
        return default

    def getAsArray(self, key, default=[]):
        ret = []
        found = False
        for v in self.values:
            if v.key == key:
                ret.append( v.value )
                found = True
        return ret if found else default

    def get_all(self):
        ret = []
        for v in self.values:
            ret.append( (v.key, v.value) )
        return ret

    def get_all_as_dict(self):
        ret = {}
        for v in self.values:
            ret[v.key] = v.value
        return ret

    def set(self, key, value, comment='', disabled=False):
        if type(value) == list:
            idx = 0
            found = 0
            last = -1
            num_values = len(value)
            i = 0
            for v in iter(self.values):
                if v.key == key:
                    if idx < num_values:
                        v.value = value[idx]
                        if type(comment) == list:
                            v.comment = comment[idx]
                        else:
                            v.comment = comment
                        if type(disabled) == list:
                            v.disabled = disabled[idx]
                        else:
                            v.disabled = disabled
                        v.original = None
                        idx += 1
                        found += 1
                        last = i
                    else:
                        self.values.remove(v)
                i += 1
            if found < num_values:
                for idx in range(found, num_values):
                    if type(comment) == list:
                        c = comment[idx]
                    else:
                        c = comment
                    if type(disabled) == list:
                        d = disabled[idx]
                    else:
                        d = disabled
                    iniline = IniSection.IniLine(self.inifile, -1, None, key, value[idx], c, d)
                    if last < 0:
                        self.values.append(iniline)
                    else:
                        self.values.insert(last, iniline)
                        last += 1
            ret = True
        else:
            found = False
            for v in self.values:
                if v.key == key:
                    if found == False:
                        v.original = None
                        v.value = value
                        v.comment = comment
                        v.disabled = disabled
                        found = True
                    else:
                        del(v)
            if found == False:
                self.values.append(IniSection.IniLine(self.inifile, -1, None, key, value, comment, disabled))
            ret = True
        return ret

    def _getLast(self, key):
        ret = None
        for v in self.values:
            if v.key == key:
                ret = v
                break
        return ret

    def append(self, key, value, comment='', disabled=False):
        self.values.append(IniSection.IniLine(self.inifile, -1, None, key, value, comment, disabled))

    def appendRaw(self, lineno, line, key, value, comment, disabled):
        self.values.append(IniSection.IniLine(self.inifile, lineno, line, key, value, comment, disabled))

    def remove(self, key):
        found = False
        for v in self.values:
            if v.key == key:
                found = True
                self.values.remove(v)
                break
        return found

    def merge(self, another_section):
        ret = True
        for v in another_section.values:
            if not self.set(v.key, v.value, v.comment, v.disabled):
                ret = False
                break
        return ret

    def clear(self):
        self.lineno = -1
        self.original = None
        self.values = []
        self.comment = ''

    @property
    def empty(self):
        return True if len(self.values) == 0 else False

    @property
    def comments(self):
        ret = []
        for value in self.values:
            if value.comment is not None and len(value.comment) != 0:
                ret.append(value.comment)
        return ret

    def replace_comment(self, comment, new_comment):
        ret = False
        for value in iter(self.values):
            if value.comment is not None and value.comment == comment:
                value.original = None
                value.comment = new_comment
                ret = True
        return ret


    def asString(self, only_data=False):
        if self.original is not None and not only_data:
            ret = self.original + '\n'
        else:
            if self.name is not None:
                ret = '[' + self.name + ']';
            else:
                ret = ''
            if not only_data:
                if len(self.comment) > 0:
                    ret += ' ' + self.inifile.m_commentPrefix + self.comment + '\n'
                elif len(ret) > 0:
                    ret += '\n'
            elif len(ret) > 0:
                ret += '\n'
        for v in self.values:
            ret += v.asString(only_data=only_data)
        return ret

    def __str__(self):
        return self.asString(only_data=False)

    def __repr__(self):
        return self.asString(only_data=False)

class IniFile(object):
    def __init__(self, filename=None, commentPrefix=None, keyValueSeperator=None, disabled_values=True, keyIsWord=True, autoQuoteStrings=False, qt=False):
        self.m_commentPrefix = commentPrefix
        self.m_keyValueSeperator = keyValueSeperator
        self.m_autoQuoteStrings = True if autoQuoteStrings or qt else False
        self.m_autoEscapeStrings = True if qt else False
        self.m_sections = []
        self.m_filename = filename
        self.m_last_error = None
        #
        # Regular expressions for parsing section headers and options.
        #
        self.SECTCRE = re.compile(
            r'\s*\['                              # [
            r'(?P<header>[^]]+)'                  # very permissive!
            r'\]\s*'                              # ]
            )
        if disabled_values:
            if commentPrefix:
                disabled_re = r'\s*(?P<disabled>[' + commentPrefix + ']*)'
            else:
                disabled_re = r'\s*(?P<disabled>[#;]*)'
        else:
            disabled_re = r''
        if qt:
            key_re = r'[\w\\]+'
        elif keyIsWord:
            key_re = r'[\w]+'
        else:
            comment_chars = commentPrefix if commentPrefix else '#;'
            if keyValueSeperator:
                key_re = r'[^' + keyValueSeperator + comment_chars + ']'
            else:
                key_re = r'[^:= \t' + comment_chars + ']'
        if keyValueSeperator:
            key_and_value_separator_re = r'\s*(?P<option>' + key_re + '[^' + keyValueSeperator + ']*)(?P<vi>[' + keyValueSeperator + '])'
        else:
            # very permissive!
            # any number of space/tab,
            # followed by separator
            # (either : or =), followed
            # by any # space/tab
            key_and_value_separator_re = r'\s*(?P<option>' + key_re + '[^:= \t]*)' \
                     r'\s*(?P<vi>[:=])\s*'
        self.OPTCRE = re.compile(
            disabled_re + 
            key_and_value_separator_re +
            r'(?P<value>.*)$' # everything up to eol is the value
            )
        if commentPrefix:
            self.COMMENTRE = re.compile(
                r'\s*(?P<commentchar>[' + commentPrefix + '])\s*(?P<comment>.*)'
                )
        else:
            self.COMMENTRE = re.compile(
                r'\s*(?P<commentchar>[#;])\s*(?P<comment>.*)'
                )
        #print('OPTCRE=' + str(self.OPTCRE.pattern))
        #print('COMMENTRE=' + str(self.COMMENTRE.pattern))

        if filename is not None:
            self._open(filename)

    def _open(self, filename):
        try:
            f = open(filename, 'r')
            self._read(f)
            f.close()
            ret = True
        except IOError as e:
            self.m_last_error = e
            ret = False
        return ret
        
    def open(self, filename=None):
        if filename is None:
            filename = self.m_filename
        if hasattr(filename , 'read'):
            self._read(filename)
            ret = True
        else:
            ret = self._open(filename)
            if not ret:
                self.m_sections = []
        return ret

    def close(self):
        self.m_sections = []
        self.m_commentPrefix = None
        self.m_keyValueSeperator = None
        self.m_last_error = None
        
    def clone(self):
        ret = IniFile(filename=None, commentPrefix=self.m_commentPrefix, keyValueSeperator=self.m_keyValueSeperator, 
                      disabled_values=True, keyIsWord=True, autoQuoteStrings=self.m_autoQuoteStrings)
        ret.SECTCRE = self.SECTCRE
        ret.OPTCRE = self.OPTCRE
        ret.COMMENTRE = self.COMMENTRE
        ret.m_sections = []
        for section in iter(self.m_sections):
            newsection = section.clone()
            newsection.inifile = ret
            ret.m_sections.append(newsection)
        return ret

    @property
    def filename(self):
        return self.m_filename
    @property
    def last_error(self):
        return self.m_last_error

    @property
    def commentPrefix(self):
        return self.m_commentPrefix

    @property
    def keyValueSeperator(self):
        return self.m_keyValueSeperator

    def _getSection(self, name):
        for section in self.m_sections:
            if section.name == name:
                return section
        return None

    def _read(self, file):
        """Parse a sectioned setup file.

        The sections in setup file contains a title line at the top,
        indicated by a name in square brackets (`[]'), plus key/value
        options lines, indicated by `name: value' format lines.
        Continuations are represented by an embedded newline then
        leading whitespace.  Blank lines, lines beginning with a '#',
        and just about everything else are ignored.
        """
        commentPrefix = self.m_commentPrefix
        commentPrefixLen = 0 if commentPrefix is None else len(commentPrefix)
        keyValueSeperator = self.m_keyValueSeperator
        #print('commentPrefix='+str(commentPrefix))
        #print('keyValueSeperator='+str(keyValueSeperator))

        cursect = None                            # None, or a dictionary
        optname = None
        lineno = 0
        e = None                                  # None, or an exception
        for line in file:
            # comment or blank line?
            if line.strip() == '': # or line[0] in '#;':
                if cursect is None:
                    cursect = IniSection(self, None, lineno)
                    self.m_sections.append(cursect)
                cursect.appendRaw(lineno, line.rstrip('\n'), None, None, None, False)
                lineno = lineno + 1
                optname = None
                continue
            # continuation line?
            if False and line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    inival = cursect._getLast(optname)
                    inival.value = "%s\n%s" % (inival.value, value)
            # a section header or option header?
            else:
                line = line.rstrip('\n')
                # is it a section header?
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    cursect = self._getSection(sectname)
                    if cursect is None:
                        cursect = IniSection(self, sectname, lineno, line)
                        self.m_sections.append(cursect)
                    # So sections can't start with a continuation line
                    optname = None
                else:
                    if cursect is None:
                        cursect = IniSection(self, None, lineno)
                        self.m_sections.append(cursect)
                    mo = self.OPTCRE.match(line)
                    if mo:
                        try:
                            disabled = mo.group('disabled')
                            if len(disabled) > 0:
                                disabled = True
                            else:
                                disabled = False
                        except IndexError:
                            disabled = False
                        optname, vi, optval = mo.group('option', 'vi', 'value')

                        if keyValueSeperator is None:
                            keyValueSeperator = vi
                            #print('got keyValueSeperator : \'' + keyValueSeperator + '\'')
                            gotValue = True
                        elif vi == keyValueSeperator:
                            gotValue = True
                        else:
                            #print('keyValueSeperator changed: \'' + keyValueSeperator + '\' to \'' + vi + '\'')
                            #print('line: ' + line)
                            gotValue = False
                    else:
                        gotValue = False

                    if gotValue:
                        if commentPrefix is None:
                            # no comment char has yet been determined or specified,
                            # so we should try to automatically detect the comment
                            # char, which can either be a semi-colon or a hash char.
                            # the comment char must be preceeded by a space char
                            pos = optval.find(';')
                            if pos != -1 and optval[pos-1].isspace():
                                commentPrefix = ';'
                            else:
                                pos = optval.find('#')
                                if pos != -1 and optval[pos-1].isspace():
                                    commentPrefix = '#'

                        if commentPrefix is not None:
                            # ';' or '#' is a comment delimiter only if it follows
                            # a spacing character
                            pos = optval.find(commentPrefix)
                            if pos != -1 and optval[pos-1].isspace():
                                optval = optval[:pos]
                                optcomment = optval[pos+1:]
                            else:
                                optcomment=None
                        else:
                            optcomment=None
                        #print('commentPrefix=' + str(commentPrefix) + ' optcomment=' + str(optcomment))

                        optval = optval.strip()
                        if self.m_autoQuoteStrings:
                            optval = unquote_string(optval)
                        else:
                            # allow empty values
                            if optval == '""':
                                optval = ''
                        if self.m_autoEscapeStrings:
                            optval = unescape_string_from_c(optval)
                        optname = optname.rstrip()

                        cursect.appendRaw(lineno, line, optname, optval, optcomment, disabled)
                    else:
                        #print('try to match comment for line: ' + line)
                        mo = self.COMMENTRE.match(line)
                        if mo:
                            (commentchar, comment) = mo.group('commentchar', 'comment')
                            if commentPrefix is None:
                                commentPrefix = commentchar
                            #print('found comment line: ' + comment)
                            cursect.appendRaw(lineno, line, None, None, comment, False)
                        else:
                            cursect.appendRaw(lineno, line, None, None, None, False)
                            #print 'unrecognized line:' + line
            lineno = lineno + 1
        if commentPrefix is not None:
            self.m_commentPrefix = commentPrefix
        else:
            self.m_commentPrefix = ';'
        if keyValueSeperator is not None:
            self.m_keyValueSeperator = keyValueSeperator
        else:
            self.m_keyValueSeperator = '='

    def get(self, section, key, default=''):
        ret = default
        section_obj = self._getSection(section)
        if section_obj is not None:
            ret = section_obj.get(key, default)
        return ret

    def getAsBoolean(self, section, key, default=None):
        value = self.get(section, key, default)
        if value is not None:
            try:
                num = int(value)
                ret = True if num != 0 else False
            except ValueError:
                str = value.lower()
                if str == 'true' or str == 'yes' or str == 'on':
                    ret = True
                elif str == 'false' or str == 'no' or str == 'off':
                    ret = False
                else:
                    ret = default
        else:
            ret = default
        return ret

    def getAsInteger(self, section, key, default=None):
        value = self.get(section, key, default)
        if value is not None:
            try:
                ret = int(value)
            except ValueError:
                ret = default
        else:
            ret = default
        return ret

    def getAsArray(self, section, key, default=[]):
        ret = default
        section_obj = self._getSection(section)
        if section_obj is not None:
            ret = section_obj.getAsArray(key, default)
        return ret

    def getAsDateTime(self, section, key, default=None, date_format='%a, %d %b %Y %H:%M:%S %z'):
        value = self.get(section, key, default)
        if value is not None:
            if isinstance(value, datetime.datetime):
                ret = value
            else:
                try:
                    ret = datetime.datetime.strptime(value)
                except ValueError:
                    ret = default
        else:
            ret = default
        return ret

    def getAsTimestamp(self, section, key, default=None):
        value = self.get(section, key, default)
        if value is not None:
            if isinstance(value, datetime.datetime):
                ret = value
            else:
                try:
                    num = float(value)
                    ret = datetime.datetime.fromtimestamp(num)
                except ValueError:
                    ret = default
        else:
            ret = default
        return ret

    def set(self, section, key, value, comment=None):
        section_obj = self._getSection(section)
        if section_obj is None:
            self.m_sections.append( IniSection(self, section) )
            section_obj = self._getSection(section)
        return section_obj.set(key, value, comment)

    def setAsBoolean(self, section, key, value, comment=None):
        if value is not None:
            real_value = 'true' if value else 'false'
        else:
            real_value = None
        return self.set(section, key, real_value, comment)

    def setAsInteger(self, section, key, value, comment=None):
        if value is not None:
            real_value = str(value)
        else:
            real_value = None
        return self.set(section, key, real_value, comment)

    def setAsDateTime(self, section, key, value, comment=None, date_format='%a, %d %b %Y %H:%M:%S %z'):
        if value is not None:
            if isinstance(value, datetime.datetime):
                real_value = value.strftime(date_format)
            elif isinstance(value, datetime.date):
                tmp_value = datetime.datetime.combine(value, datetime.time.min)
                real_value = tmp_value.strftime(date_format)
            elif isinstance(value, datetime.time):
                tmp_value = datetime.datetime.combine(datetime.date.min, value)
                real_value = tmp_value.strftime(date_format)
            else:
                raise ValueError
        else:
            real_value = None
        return self.set(section, key, real_value, comment)

    def setAsTimestamp(self, section, key, value, comment=None):
        if value is not None:
            if isinstance(value, datetime.datetime):
                real_value = timestamp_from_datetime(value)
            elif isinstance(value, datetime.date):
                tmp_value = datetime.datetime.combine(value, time.min)
                real_value = timestamp_from_datetime(tmp_value)
            elif isinstance(value, datetime.time):
                real_value = value.time()
            else:
                raise ValueError
        else:
            real_value = None
        return self.set(section, key, real_value, comment)

    def append(self, section, key, value, comment=None):
        section_obj = self._getSection(section)
        if section_obj is None:
            self.m_sections.append( IniSection(self, section) )
            section_obj = self._getSection(section)
        return section_obj.append(key, value, comment)

    def remove(self, section, key):
        ret = False
        for section_obj in self.m_sections:
            if section_obj.name == section:
                if key == '*':
                    self.m_sections.remove(section_obj)
                    ret = True
                else:
                    ret = section_obj.remove(key)
                break
        return ret

    def has_section(self, section):
        section_obj = self._getSection(section)
        return True if section_obj is not None else False

    def section(self, section):
        return self._getSection(section)

    @property
    def empty(self):
        ret = True
        for section_obj in self.m_sections:
            if not section_obj.empty:
                ret = False
                break
        return ret

    @property
    def sections(self):
        ret = []
        for section_obj in self.m_sections:
            ret.append(section_obj.name)
        return ret

    @property
    def comments(self):
        ret = []
        for section_obj in self.m_sections:
            ret.extend(section_obj.comments)
        return ret

    def replace_comment(self, comment, new_comment):
        ret = False
        for section_obj in iter(self.m_sections):
            if section_obj.replace_comment(comment, new_comment):
                ret = True
        return ret

    def __str__(self):
        return self.asString(only_data=False)

    def asString(self, only_data=False):
        ret = ''
        for section in self.m_sections:
            ret += section.asString(only_data=only_data)
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.m_filename
        
        if hasattr(filename, 'write'):
            f = filename
        else:
            try:
                f = open(filename, 'w')
            except IOError as e:
                self.m_last_error = e
                f = None
        if f:
            try:
                for section in self.m_sections:
                    f.write(str(section))
                ret = True
            except IOError as e:
                self.m_last_error = e
                ret = False
            if not hasattr(filename, 'write'):
                f.close()
        else:
            ret = False
        return ret

    def merge(self, another_inifile):
        ret = True
        #print('merge ' + another_inifile.m_filename + ' into ' + self.m_filename)
        #print(another_inifile.m_sections)
        for section_obj in another_inifile.m_sections:
            my_section_obj = self._getSection(section_obj.name)
            if my_section_obj is None:
                #print('create new section ' + section_obj.name)
                self.m_sections.append( IniSection(self, section_obj.name) )
                my_section_obj = self._getSection(section_obj.name)
            ret = my_section_obj.merge(section_obj)
            if not ret:
                break
        return ret

    def replace(self, another_inifile):
        ret = True
        for section_obj in another_inifile.m_sections:
            my_section_obj = self._getSection(section_obj.name)
            #print('replace section ' + str(section_obj.name))
            if my_section_obj is not None:
                my_section_obj.clear()
            else:
                # add a new section because it's missing
                self.m_sections.append( IniSection(self, section_obj.name) )
                my_section_obj = self._getSection(section_obj.name)
            ret = my_section_obj.merge(section_obj)
            if not ret:
                break
        return ret


class IniFileDirectory(object):

    def __init__(self, directory=None, config_extension=None, 
                 commentPrefix=None, keyValueSeperator=None, disabled_values=True, keyIsWord=True, autoQuoteStrings=False):
        self.directory = directory
        self.config_extension = config_extension
        self.commentPrefix = commentPrefix
        self.keyValueSeperator = keyValueSeperator
        self.disabled_values = disabled_values
        self.keyIsWord = keyIsWord
        self.autoQuoteStrings = autoQuoteStrings
        if self.directory is not None:
            self._load()
        else:
            self._items = []

    def _load(self):
        # load the the config files in the directory
        try:
            self._items = []
            ret = True
            files = os.listdir(self.directory)
            for f in files:
                if self.config_extension is None:
                    load_file = True
                else:
                    (basename, ext) = os.path.splitext(f)
                    load_file = True if ext == self.config_extension else False
                if load_file:
                    fullpath = os.path.join(self.directory, f)
                    item = IniFile(fullpath, 
                                   commentPrefix=self.commentPrefix, 
                                   keyValueSeperator=self.keyValueSeperator, 
                                   disabled_values=self.disabled_values, 
                                   keyIsWord=self.keyIsWord, 
                                   autoQuoteStrings=self.autoQuoteStrings)
                    self._items.append(item)
        except (IOError, OSError) as e:
            self._last_error = str(e)
            ret = False

        return ret

    @property
    def empty(self):
        ret = True
        for item in self._items:
            if not item.empty:
                ret = False
                break
        return ret

    @property
    def sections(self):
        ret = []
        for item in self._items:
            ret.extend(item.sections)
        return ret

    @property
    def comments(self):
        ret = []
        for item in self._items:
            ret.extend(item.comments)
        return ret

    @property
    def items(self):
        return self._items

    def getAsArray(self, section, key, default=[]):
        ret = []
        got_one_value = False
        for item in self._items:
            item_ret = item.getAsArray(section, key, None)
            if item_ret:
                got_one_value = True
                ret.extend(item_ret)
        if got_one_value:
            return ret
        else:
            return default
