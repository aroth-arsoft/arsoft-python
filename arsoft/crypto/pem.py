#!/usr/bin/python
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

    s_begin_or_end_pattern = re.compile('^-----(?P<cmd>BEGIN|END) (?P<type>[A-Za-z ]+)-----$')
    def __init__(self, filename=None, passphrase=None):
        self.m_filename = filename
        self.m_passphrase = passphrase
        self.m_blocks = []
        
    def open(self, filename=None, passphrase=None):
        if filename is None:
            filename = self.m_filename
        if passphrase is None:
            passphrase = self.m_passphrase

        ret = False
        blockdata = ''
        blocktype = None
        lineno = 0
        try:
            f = open(filename, 'r')
            for line in f:
                result = self.s_begin_or_end_pattern.match(line)
                if result is not None:
                    cmd = result.group('cmd')
                    blocktype = result.group('type')
                    if cmd == "BEGIN":
                        # clear the cert buffer
                        blockdata = ''
                        blockdata += line
                    elif cmd == "END":
                        if blocktype:
                            blockdata += line
                            blockindex = len(self.m_blocks)
                            self.m_blocks.append( PEMItem(blockindex, blocktype, blockdata) )
                        # prepare for next cert
                        blocktype = None
                        blockdata = ''
                else:
                    if blocktype:
                        blockdata += line
                lineno = lineno + 1
            f.close()
            ret = True
        except:
            ret = False
            pass
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
        except:
            ret = False
            pass
        return ret
        
    def close(self):
        self.m_filename = None
        self.m_passphrase = None
        self.m_blocks = []
        
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
