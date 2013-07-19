#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import socket, ssl
from urlparse import urlparse
from pem import *
from OpenSSL import crypto
from arsoft.timestamp import parse_date
from arsoft.utils import detect_file_type


class CRL(PEMItem):
    def __init__(self, pemitem=None, rawitem=None):
        self._rev_list = None
        if pemitem:
            PEMItem.__init__(self, pemitem.blockindex, pemitem.blocktype, pemitem.blockdata)
            self.crl = crypto.load_crl(crypto.FILETYPE_PEM, pemitem.blockdata) 
        else:
            PEMItem.__init__(self, 0, 'X509 CRL', None)
            self.crl = None

    @property
    def revoked(self):
        if self._rev_list is None:
            self._rev_list = []
            for rev in self.crl.get_revoked():
                self._rev_list.append(CRL.RevokeItem(rev))
        return self._rev_list

    class RevokeItem(object):
        def __init__(self, rev):
            self._rev = rev
        @property
        def serial(self):
            return int(self._rev.get_serial(), 16)
        @property
        def reason(self):
            return self._rev.get_reason()
        @property
        def revoke_date(self):
            return parse_date(self._rev.get_rev_date())

    def writePretty(self, fobj, indent=0, filename=None, crlno=None, short=False):
        prefix = ' ' * indent

        if short:
            fobj.write(filename + '\n')
        else:
            if filename:
                if crlno:
                    fobj.write(prefix + 'CRL %s #%i:\n' %(filename, crlno))
                else:
                    fobj.write(prefix + 'CRL %s:\n' %(filename))
            else:
                if crlno:
                    fobj.write(prefix + 'CRL #%i:\n' %(crlno))
                else:
                    fobj.write(prefix + 'CRL:\n')
            for rev in self.revoked:
                fobj.write(prefix + "  Serial %i (0x%X), reason %s at %s\n" % (rev.serial, rev.serial, rev.reason, rev.revoke_date))

class CRLPEMFile(PEMFile):
    def __init__(self, filename=None):
        PEMFile.__init__(self, filename)

    def getCRLs(self):
        ret = []
        i = 0
        while i < len(self.m_blocks):
            pemitem = self.m_blocks[i]
            if pemitem.blocktype == 'X509 CRL':
                crl = CRL(pemitem)
                ret.append( crl )
            i = i + 1
        return ret

    @property
    def crls(self):
        return self.getCRLs()

    @property
    def revoked(self):
        ret = []
        for crl in self.getCRLs():
            ret.extend(crl.revoked)
        return ret

class CRLFile(object):
    def __init__(self, filename=None):
        self.filename = filename
        self.file_type = None
        self._impl = None
        self._last_error = None
        if self.filename is not None:
            self.open()

    def open(self, filename=None):
        if filename is None:
            filename = self.filename

        if self.file_type is None:
            if hasattr(filename, 'read'):
                self.file_type = 'ASCII text'
            else:
                self.file_type = detect_file_type(filename) if filename else None
        print(self.file_type)
        if self.file_type == 'ASCII text':
            self._impl = CRLPEMFile(self.filename)
            ret = self._impl.open()
        else:
            self._last_error = TypeError('file type %s not supported' % (self.file_type))
            ret = False
        return ret

    def __str__(self):
        if self._impl:
            return str(self._impl)
        else:
            return self.__class__.__name__ + '(%s)' % (self.filename)

    def close(self):
        if self._impl:
            self._impl.close()
            self._impl = None

    @property
    def last_error(self):
        if self._impl:
            return self._impl.last_error
        else:
            return self._last_error

    @property
    def crls(self):
        if self._impl:
            return self._impl.crls
        else:
            return []

    @property
    def revoked(self):
        if self._impl:
            return self._impl.revoked
        else:
            return []

class CRLList:
    def __init__(self):
        self.m_crls = []
        
    def _getAllCRLFilesInDir(self, dirname):
        ret = []
        exclude_dirs = ['.svn', 'CVS', '.git' ]
        crl_file_exts = ['.pem', '.crt' ]
        for direntry in os.listdir(dirname):
            fullname = os.path.join(dirname, direntry)
            if os.path.isdir(fullname):
                if not direntry in exclude_dirs:
                    ret.extend( self._getAllCRLFilesInDir(fullname) )
            else:
                (basename, ext) = os.path.splitext(direntry)
                if ext in crl_file_exts:
                    ret.append(fullname)
        return ret
    
    @property
    def empty(self):
        return True if len(self.m_crls) == 0 else False

    def __getitem__(self, key):
        # if key is of invalid type or value, the list values will raise the error
        return self.m_crls[key]
    def __setitem__(self, key, value):
        self.m_crls[key] = value

    def __len__(self):
        return len(self.m_crls)
    def __iter__(self):
        return iter(self.m_crls)

    def add(self, filename):
        if os.path.isdir(filename):
            ret = self.addDirectory(filename)
        else:
            ret = self.addFile(filename)
        return ret
    
    def addFile(self, filename):
        pemfile = CRLPEMFile(filename)
        print('add file %s' % filename)
        if pemfile.open():
            for crl in pemfile.getCRLs():
                crl_tuple = (filename, crl)
                self.m_crls.append(crl_tuple)
            ret = True
        else:
            ret = False
        return ret
    
    def addDirectory(self, dirname):
        ret = False
        dir_files = self._getAllCRLFilesInDir(dirname)
        
        for file_in_dir in dir_files:
            if self.addFile(file_in_dir):
                ret = True
        return ret
        
    def write(self, fobj, output_number=True, short=False):
        num_crls = 0
        for (crlfile, crl) in self.m_crls:
            crl.writePretty(fobj, filename=crlfile, crlno=num_crls, short=short)
            num_crls = num_crls + 1

        if output_number and not short:
            fobj.write("Number of CRLs: " + str(num_crls) + "\n")

if __name__ == "__main__":
    f =  CRLFile(sys.argv[1])
    print(f)
    print(f.crls)
    for rev in f.revoked:
        print(rev.get_serial(), rev.get_reason())

