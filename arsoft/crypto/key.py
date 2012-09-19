#!/usr/bin/python

import os
from pem import *
from OpenSSL import crypto

class KeyItem(PEMItem):
    def __init__(self, pemitem, private=True, passphrase=None):
        PEMItem.__init__(self, pemitem.blockindex, pemitem.blocktype, pemitem.blockdata)
        if passphrase is None:
            self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, self.blockdata)
        else:
            self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, self.blockdata, passphrase)
        self.private=private
        
    def get_bits(self):
        return self.key.bits()

    def get_type(self):
        return self.key.type()
            
    def get_type_str(self):
        if self.key.type() == crypto.TYPE_RSA:
            return 'RSA'
        elif self.key.type() == crypto.TYPE_DSA:
            return 'DSA'
        else:
            return 'Unknown'

    @property
    def public(self):
        return True if self.private == False else False

    def writePretty(self, fobj, indent=0, filename=None, keyno=None, short=False):
        prefix = ' ' * indent

        if short:
            fobj.write(filename + '\n')
        else:
            if filename:
                if keyno:
                    fobj.write(prefix + ('Private' if self.private else 'Public') + ' Key ' + filename + " #" + str(keyno) + ":\n")
                else:
                    fobj.write(prefix + ('Private' if self.private else 'Public') + ' Key ' + filename + ":\n")
            else:
                if keyno:
                    fobj.write(prefix + ('Private' if self.private else 'Public') + ' Key #' + str(keyno) + ":\n")
                else:
                    fobj.write(prefix + ('Private' if self.private else 'Public') + " Key:\n")
            fobj.write(prefix + "  Bits: " + self.get_type_str() + '/' + str(self.get_bits()) + '\n')


class KeyList:
    def __init__(self):
        self.m_keys = []
        
    def _getAllKeyFilesInDir(self, dirname):
        ret = []
        exclude_dirs = ['.svn', 'CVS', '.git' ]
        cert_file_exts = ['.pem', '.key' ]
        for direntry in os.listdir(dirname):
            fullname = os.path.join(dirname, direntry)
            if os.path.isdir(fullname):
                if not direntry in exclude_dirs:
                    ret.extend( self._getAllKeyFilesInDir(fullname) )
            else:
                (basename, ext) = os.path.splitext(direntry)
                if ext in cert_file_exts:
                    ret.append(fullname)
        return ret
    
    @property
    def empty(self):
        return True if len(self.m_keys) == 0 else False

    def add(self, filename):
        if os.path.isdir(filename):
            ret = self.addDirectory(filename)
        else:
            ret = self.addFile(filename)
        return ret
    
    def addFile(self, filename):
        pemfile = KeyPEMFile(filename)
        if pemfile.open():
            for key in pemfile.getKeys():
                key_tuple = (filename, key)
                self.m_keys.append(key_tuple)
            ret = True
        else:
            ret = False
        return ret
    
    def addDirectory(self, dirname):
        ret = False
        dir_files = self._getAllKeyFilesInDir(dirname)
        
        for file_in_dir in dir_files:
            if self.addFile(file_in_dir):
                ret = True
        return ret
        
    def save(self):
        ret = True
        # find all unique certfiles
        unique_files = {}
        for (keyfile, key) in self.m_keys:
            if keyfile in unique_files:
                unique_files[keyfile].append(key)
            else:
                unique_files[keyfile] = [ key ]
        
        for keyfile, keylist in unique_files.iteritems():
            pemfile = PEMFile()
            for key in keylist:
                pemfile.append(key)
            ret = pemfile.save(keyfile)
        return ret
        
    def write(self, fobj, output_number=True, short=False):

        num_keys = 0
        for (keyfile, key) in self.m_keys:
            key.writePretty(fobj, filename=keyfile, keyno=num_keys, short=short)
            num_keys = num_keys + 1

        if output_number and not short:
            fobj.write("Number of keys: " + str(num_keys) + "\n")

class KeyPEMFile(PEMFile):
    def __init__(self, filename=None):
        PEMFile.__init__(self, filename)
        
    def getKeys(self):
        ret = []
        i = 0
        while i < len(self.m_blocks):
            pemitem = self.m_blocks[i]
            if pemitem.blocktype == 'RSA PRIVATE KEY' or pemitem.blocktype == 'DSA PRIVATE KEY':
                key = KeyItem(pemitem, private=True)
                ret.append( key )
            elif pemitem.blocktype == 'RSA PUBLIC KEY' or pemitem.blocktype == 'DSA PUBLIC KEY':
                key = KeyItem(pemitem, private=False)
                ret.append( key )
            i = i + 1
        return ret

 
