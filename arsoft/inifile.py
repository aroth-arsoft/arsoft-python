#!/usr/bin/python

import re

class IniValue(object):
    inifile = None
    line = -1
    key = ''
    value = ''
    comment = ''
    disabled = False
    def __init__(self, inifile, line, key, value, comment='', disabled=False):
        self.inifile = inifile
        self.line = line
        self.key = key
        self.value = value
        self.comment = comment
        self.disabled = disabled

    def __repr__(self):
        return toString()
    def toString(self):
        if self.disabled == False:
            ret = ''
        else:
            ret = self.inifile.m_commentPrefix
        if self.key is not None:
            ret += self.key + self.inifile.m_keyValueSeperator
            if self.value is not None:
                ret += self.value
        if self.comment is not None:
            if len(ret) > 0:
                ret += ' ' + self.inifile.m_commentPrefix + self.comment
            else:
                ret += self.inifile.m_commentPrefix + self.comment
        #if len(ret) > 0:
        ret += '\n'
        return ret

class IniSection(object):
    inifile = None
    name = None
    line = -1
    values = []
    comment = ''

    def __init__(self, inifile, name, line, comment=''):
        self.inifile = inifile
        self.name = name
        self.line = line
        self.comment = comment
        self.values = []
        
    def _append(self, line, key, value, comment, disabled):
        self.values.append(IniValue(self.inifile, line, key, value, comment, disabled))

    def get(self, key, default=''):
        for v in self.values:
            if v.key == key:
                return v.value
        return default

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
                    if last < 0:
                        self.values.append(IniValue(self.inifile, -1, key, value[idx], c, d))
                    else:
                        self.values.insert(last, IniValue(self.inifile, -1, key, value[idx], c, d))
                        last += 1
        else:
            found = False
            for v in self.values:
                if v.key == key:
                    if found == False:
                        v.value = value
                        v.comment = comment
                        v.disabled = disabled
                        found = True
                    else:
                        del(v)
            if found == False:
                self.values.append(IniValue(self.inifile, -1, key, value, comment, disabled))

    def _getLast(self, key):
        ret = None
        for v in self.values:
            if v.key == key:
                ret = v

    def append(self, key, value, comment='', disabled=False):
        self.values.append(IniValue(self.inifile, -1, key, value, comment, disabled))

    def remove(self, key):
        found = False
        for v in self.values:
            if v.key == key:
                del(v)
        return Found

    def __repr__(self):
        return toString()
    def toString(self):
        if self.name is not None:
            ret = '[' + self.name + ']';
        else:
            ret = ''
        if len(self.comment) > 0:
            ret += ' ' + self.inifile.m_commentPrefix + self.comment + '\n'
        elif len(ret) > 0:
            ret += '\n'
        for v in self.values:
            ret += v.toString()
        return ret

class IniFile(object):
    m_filename = ''
    m_content = []
    m_sections = {}
    m_commentPrefix = ';'
    m_keyValueSeperator = '='
    def __init__(self, filename):
        self.m_filename = filename
        try:
            f = open(filename, 'r')
            self._read(f)
            f.close()
        except IOError:
            self.m_content = []
            self.m_sections = {}

    #
    # Regular expressions for parsing section headers and options.
    #
    SECTCRE = re.compile(
        r'\['                                 # [
        r'(?P<header>[^]]+)'                  # very permissive!
        r'\]'                                 # ]
        )
    OPTCRE = re.compile(
        r'(?P<disabled>[#;]*)(?P<option>[\w]+[^:= \t]*)'          # very permissive!
        r'(?P<vi>[:= \t])'                 # any number of space/tab,
                                              # followed by separator
                                              # (either : or =), followed
                                              # by any # space/tab
        r'(?P<value>.*)$'                     # everything up to eol
        )

    def _read(self, file):
        """Parse a sectioned setup file.

        The sections in setup file contains a title line at the top,
        indicated by a name in square brackets (`[]'), plus key/value
        options lines, indicated by `name: value' format lines.
        Continuations are represented by an embedded newline then
        leading whitespace.  Blank lines, lines beginning with a '#',
        and just about everything else are ignored.
        """
        commentPrefix = None
        commentPrefixLen = 0
        keyValueSeperator = None

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
                    self.m_sections['default'] = cursect
                cursect._append(lineno, None, None, None, False)
                lineno = lineno + 1
                continue
            # continuation line?
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    inival = cursect._getLast(optname)
                    inival.value = "%s\n%s" % (iniline.value, value)
            # a section header or option header?
            else:
                line = line.rstrip('\n')
                # is it a section header?
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self.m_sections:
                        cursect = self.m_sections[sectname]
                    else:
                        cursect = IniSection(self, sectname, lineno)
                        self.m_sections[sectname] = cursect
                    # So sections can't start with a continuation line
                    optname = None
                else:
                    if cursect is None:
                        cursect = IniSection(self, None, lineno)
                        self.m_sections['default'] = cursect
                    mo = self.OPTCRE.match(line)
                    if mo:
                        disabled, optname, vi, optval = mo.group('disabled','option', 'vi', 'value')
                        if keyValueSeperator is None:
                            keyValueSeperator = vi
                        elif vi != keyValueSeperator:
                            raise UnknownError

                        if commentPrefix is None:
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

                        optval = optval.strip()
                        # allow empty values
                        if optval == '""':
                            optval = ''
                        optname = optname.rstrip()

                        if len(disabled) > 0:
                            disabled = True
                        else:
                            disabled = False
                        cursect._append(lineno, optname, optval, optcomment, disabled)
                    else:
                        if commentPrefix is None:
                            if line[0] in ';#':
                                commentPrefix = line[0]
                                commentPrefixLen = len(commentPrefix)
                        if line[0:commentPrefixLen] == commentPrefix:
                            cursect._append(lineno, None, None, line[commentPrefixLen:], False)
                        else:
                            print 'unrecognized line:' + line
            lineno = lineno + 1
            self.m_commentPrefix = commentPrefix
            self.m_keyValueSeperator = keyValueSeperator

    def get(self, section, key, default=''):
        ret = default
        if section in self.m_sections:
            ret = self.m_sections[section].get(key, default)
        return ret

    def set(self, section, key, value, comment=None):
        if section not in self.m_sections:
            self.m_sections[section] = IniSection(sectname, lineno)
        self.m_sections[section].set(key, value, comment)
    
    def append(self, section, key, value, comment=None):
        if section not in self.m_sections:
            self.m_sections[section] = IniSection(sectname, lineno)
        self.m_sections[section].append(key, value, comment)

    def has_section(self, section):
        if section in self.m_sections:
            return True
        else:
            return False

    def __repr__(self):
        ret = ''
        for (name,section) in self.m_sections.items():
            ret += section.toString()
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.m_filename
        f = open(filename, 'w')
        for (name,section) in self.m_sections.items():
            s = section.toString()
            f.write(s)
        f.close()
