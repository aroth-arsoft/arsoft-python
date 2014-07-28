#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
import sys
import re
import io
import hashlib

class PEMItem(object):
    def __init__(self, blockindex, blocktype, blockdata):
        self.blockindex = blockindex
        self.blocktype = blocktype
        self.blockdata = blockdata
        
    def write(self, fobj):
        fobj.write(self.blockdata)
        
    def getHash(self):
        m = hashlib.md5()
        m.update(self.blockdata)
        return m.hexdigest()
        
class PEMFile:

    s_begin_or_end_pattern = re.compile('^-----(?P<cmd>BEGIN|END) (?P<type>[A-Za-z0-9 ]+)-----$')
    def __init__(self, filename=None, passphrase=None):
        self.m_filename = filename
        self.m_passphrase = passphrase
        self.m_blocks = []
        self.m_last_error = None

    def __str__(self):
        return self.__class__.__name__ + '(%s)' % (self.m_filename)

    def open(self, filename=None, passphrase=None):
        if filename is None:
            filename = self.m_filename
        if passphrase is None:
            passphrase = self.m_passphrase

        ret = False
        blockdata = ''
        blocktype = None
        lineno = 0
        close_file_required = False
        try:
            ret = True
            if hasattr(filename, 'read'):
                f = filename
            else:
                f = open(filename, 'rU')
                close_file_required = True if f else False
        except IOError as e:
            self.m_last_error = e
            ret = False
        if ret:
            try:
                for line in f:
                    #print('got line ' + line)
                    result = self.s_begin_or_end_pattern.match(line)
                    if result is not None:
                        cmd = result.group('cmd')
                        blocktype = result.group('type')
                        #print('got %s type %s' % (cmd, blocktype))
                        if cmd == "BEGIN":
                            # clear the cert buffer
                            #print('got blockstart ' + blocktype)
                            blockdata = ''
                            blockdata += line
                        elif cmd == "END":
                            #print('got blockend ' + blocktype)
                            if blocktype:
                                blockdata += line
                                blockindex = len(self.m_blocks)
                                self.m_blocks.append( PEMItem(blockindex, blocktype, blockdata) )
                            # prepare for next cert
                            blocktype = None
                            blockdata = ''
                        else:
                            #print('unexpected block')
                            ret = False
                            break
                    else:
                        if blocktype:
                            blockdata += line
                    lineno = lineno + 1
            except IOError as e:
                self.m_last_error = e
                ret = False
                pass
        if close_file_required:
            f.close()
        return ret

    def save(self, filename=None):
        if filename is None:
            filename = self.m_filename

        try:
            f = open(filename, 'w')
            for pemitem in self.m_blocks:
                pemitem.write(f)
            f.close()
            ret = True
        except IOError as e:
            self.m_last_error = e
            ret = False
            pass
        return ret
        
    def close(self):
        self.m_filename = None
        self.m_passphrase = None
        self.m_blocks = []
        self.m_last_error = None

    @property
    def filename(self):
        return self.m_filename

    @property
    def last_error(self):
        return self.m_last_error

    @property
    def valid(self):
        return True if self.m_filename is not None and self.m_last_error is None else False

    def getBlocks(self, blocktype):
        ret = []
        for pemitem in self.m_blocks:
            if pemitem.blocktype == blocktype:
                ret.append(pemitem)
        return ret
        
    def appendBlock(self, blocktype, blockdata):
        blockindex = len(self.m_blocks)
        self.m_blocks.append( PEMItem(blockindex, blocktype, blockdata) )

    def append(self, pemitem):
        self.m_blocks.append( pemitem )
