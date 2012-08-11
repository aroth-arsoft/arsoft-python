#!/usr/bin/python

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

        def __str__(self):
            if self.original is not None:
                ret = self.original
            else:
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
                del(v)
                break
        return found

    def __str__(self):
        if self.original is not None:
            ret = self.original + '\n'
        else:
            if self.name is not None:
                ret = '[' + self.name + ']';
            else:
                ret = ''
            if len(self.comment) > 0:
                ret += ' ' + self.inifile.m_commentPrefix + self.comment + '\n'
            elif len(ret) > 0:
                ret += '\n'
        for v in self.values:
            ret += str(v)
        return ret

class IniFile(object):
    m_filename = ''
    m_content = []
    m_sections = []
    m_commentPrefix = ';'
    m_keyValueSeperator = '='
    def __init__(self, filename=None, commentChars=[';', '#']):
        if filename is not None:
            self.open(filename)
    #
    # Regular expressions for parsing section headers and options.
    #
    SECTCRE = re.compile(
        r'\s*\['                              # [
        r'(?P<header>[^]]+)'                  # very permissive!
        r'\]\s*'                              # ]
        )
    OPTCRE = re.compile(
        r'\s*(?P<disabled>[#;]*)\s*(?P<option>[\w]+[^:= \t]*)'          # very permissive!
        r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
                                              # followed by separator
                                              # (either : or =), followed
                                              # by any # space/tab
        r'(?P<value>.*)$'                     # everything up to eol
        )
    COMMENTRE = re.compile(
        r'\s*(?P<commentchar>[#;])\s*(?P<comment>.*)'
        )
        
    def open(self, filename):
        try:
            f = open(filename, 'r')
            self._read(f)
            f.close()
            self.m_filename = filename
            ret = True
        except IOError:
            self.m_content = []
            self.m_sections = []
            self.m_filename = None
            ret = False
        return ret
        
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
                    self.m_sections.append(cursect)
                cursect.appendRaw(lineno, line, None, None, None, False)
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
                        disabled, optname, vi, optval = mo.group('disabled','option', 'vi', 'value')
                        if keyValueSeperator is None:
                            keyValueSeperator = vi
                        elif vi.strip() != keyValueSeperator:
                            print('keyValueSeperator changed: ' + keyValueSeperator + ' to ' + vi.strip())
                            print('line: ' + line)
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
            self.m_commentPrefix = commentPrefix
            self.m_keyValueSeperator = keyValueSeperator

    def get(self, section, key, default=''):
        ret = default
        section_obj = self._getSection(section)
        if section_obj is not None:
            ret = section_obj.get(key, default)
        return ret

    def set(self, section, key, value, comment=None):
        section_obj = self._getSection(section)
        if section_obj is None:
            self.m_sections.append( IniSection(self, sectname) )
            section_obj = self._getSection(section)
        return section_obj.set(key, value, comment)

    def append(self, section, key, value, comment=None):
        section_obj = self._getSection(section)
        if section_obj is None:
            self.m_sections.append( IniSection(self, sectname) )
            section_obj = self._getSection(section)
        return section_obj.append(key, value, comment)
    
    def remove(self, section, key, comment=None):
        section_obj = self._getSection(section)
        if section_obj is not None:
            return section_obj.remove(key, value, comment)
        else:
            return True

    def has_section(self, section):
        section_obj = self._getSection(section)
        return True if section_obj is not None else False

    def __str__(self):
        ret = ''
        for section in self.m_sections:
            ret += str(section)
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.m_filename
        f = open(filename, 'w')
        for section in self.m_sections:
            f.write(str(section))
        f.close()
