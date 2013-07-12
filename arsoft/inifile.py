#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re

class IniSection(object):
    inifile = None
    name = None
    lineno = -1
    original = None
    values = []
    comment = ''

    def __init__(self, inifile, name, lineno=-1, original=None, comment=''):
        self.inifile = inifile
        self.name = name
        self.lineno = lineno
        self.original = original
        self.comment = comment
        self.values = []

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

    def set(self, key, value, comment='', disabled=False):
        if type(value) == type([]):
            idx = 0
            found = 0
            last = -1
            #print 'set ' + key + ' ' + str(value)
            for i in range(0, len(self.values) - 1):
                v = self.values[i]
                if v.key == key:
                    if idx < len(value):
                        #print 'set value ' + str(idx) + ' ' + value[idx]
                        v.value = value[idx]
                        if type(comment) == type([]):
                            v.comment = comment[idx]
                        else:
                            v.comment = comment
                        if type(disabled) == type([]):
                            v.disabled = disabled[idx]
                        else:
                            v.disabled = disabled
                        idx += 1
                        found += 1
                        last = i
                    else:
                        del(v)
            #print 'found ' + str(found)
            if found < len(value):
                for idx in range(found, len(value) - 1):
                    #print 'add ' + str(idx) + ' ' + value[idx]
                    if type(comment) == type([]):
                        c = comment[idx]
                    else:
                        c = comment
                    if type(disabled) == type([]):
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
    def __init__(self, filename=None, commentPrefix=None, keyValueSeperator=None, disabled_values=True, keyIsWord=True, autoQuoteStrings=False):
        self.m_commentPrefix = commentPrefix
        self.m_keyValueSeperator = keyValueSeperator
        self.m_autoQuoteStrings = autoQuoteStrings
        self.m_content = []
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
        if keyIsWord:
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
            filename = self._m_filename
        if hasattr(filename , 'read'):
            self._read(filename)
            ret = True
        else:
            ret = self._open(filename)
            if not ret:
                self.m_content = []
                self.m_sections = []
        return ret

    def close(self):
        self.m_content = []
        self.m_sections = []
        self.m_commentPrefix = None
        self.m_keyValueSeperator = None
        self.m_last_error = None

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
        self.m_content = []
        for line in file:
            self.m_content.append(line)
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
                        # allow empty values
                        if optval == '""':
                            optval = ''
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

    def getAsArray(self, section, key, default=[]):
        ret = default
        section_obj = self._getSection(section)
        if section_obj is not None:
            ret = section_obj.getAsArray(key, default)
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
        print('ini save to ', filename)
        try:
            f = open(filename, 'w')
            for section in self.m_sections:
                f.write(str(section))
            f.close()
            ret = True
        except IOError as e:
            print('got error %s' %e)
            self.m_last_error = e
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
