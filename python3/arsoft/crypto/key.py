#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
from .pem import *
from OpenSSL import crypto

class PrivateKeyError(Exception):
    def __str__(self):
        return 'Error: Wrong private key'

class PublicKeyError(Exception):
    def __str__(self):
        return 'Error: Invalid public key'

class KeyItem(PEMItem):

    @staticmethod
    def _empty_passphrase_callback(*args):
        return b''
    def __init__(self, pemitem, private=True, passphrase=None):
        PEMItem.__init__(self, pemitem.blockindex, pemitem.blocktype, pemitem.blockdata)
        if private:
            try:
                if passphrase is None:
                    self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, pemitem.blockdata, KeyItem._empty_passphrase_callback)
                else:
                    self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, pemitem.blockdata, passphrase)
            except crypto.Error as e:
                raise PrivateKeyError
        else:
            try:
                self.key = crypto.load_publickey(crypto.FILETYPE_PEM, pemitem.blockdata)
            except crypto.Error as e:
                raise PublicKeyError
        self.private=private
        
    def get_bits(self):
        return self.key.bits()

    @property
    def bits(self):
        return self.key.bits()

    def get_type(self):
        return self.key.type()

    @property
    def type(self):
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

    def export(self, passphrase=None, cipher='blowfish', encoding='utf8'):
        if passphrase is None:
            return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key, cipher=cipher)
        else:
            return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key, cipher=cipher, passphrase=bytes(passphrase, encoding=encoding) if isinstance(passphrase,str) else passphrase)

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

    def __getitem__(self, key):
        # if key is of invalid type or value, the list values will raise the error
        return self.m_keys[key]
    def __setitem__(self, key, value):
        self.m_keys[key] = value

    def __len__(self):
        return len(self.m_keys)
    def __iter__(self):
        return iter(self.m_keys)

    def add(self, filename):
        call_add_file_or_dir = True
        if '://' in filename:
            (schema, rest) = filename.split('://', 2)
            if schema == 'file':
                filename = rest
            else:
                call_add_file_or_dir = False
                ret = False
        if call_add_file_or_dir:
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
        
        for keyfile, keylist in unique_files.items():
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
    def __init__(self, filename=None, passphrase=None):
        PEMFile.__init__(self, filename, passphrase)
        
    def getKeys(self):
        ret = []
        i = 0
        while i < len(self.m_blocks):
            pemitem = self.m_blocks[i]
            if pemitem.blocktype == 'RSA PRIVATE KEY' or pemitem.blocktype == 'DSA PRIVATE KEY' or pemitem.blocktype == 'PRIVATE KEY' or pemitem.blocktype == 'ENCRYPTED PRIVATE KEY':
                key = KeyItem(pemitem, private=True, passphrase=self.m_passphrase)
                ret.append( key )
            elif pemitem.blocktype == 'RSA PUBLIC KEY' or pemitem.blocktype == 'DSA PUBLIC KEY' or pemitem.blocktype == 'PUBLIC KEY' or pemitem.blocktype == 'ENCRYPTED PUBLIC KEY':
                key = KeyItem(pemitem, private=False, passphrase=self.m_passphrase)
                ret.append( key )
            i = i + 1
        return ret

    @property
    def keys(self):
        return self.m_keys
 
    def export(self, filename, passphrase=None, encoding='utf8'):
        if filename is None:
            filename = self.m_filename

        if hasattr(filename, 'write'):
            call_file_close = False
            f = filename
        else:
            call_file_close = True
            try:
                f = open(filename, 'w')
            except IOError as e:
                self.m_last_error = e
                f = None
        if f:
            for pemitem in self.m_blocks:
                keyitem = KeyItem(pemitem)
                keyblock = keyitem.export(passphrase, encoding=encoding)
                f.write(keyblock)
            if call_file_close:
                f.close()
            ret = True
        else:
            ret = False
        return ret

def compare_pem_key(key_a, key_b, passphrase=None, encoding='utf8'):
    if passphrase is not None:
        pw = passphrase=bytes(passphrase, encoding=encoding) if isinstance(passphrase,str) else passphrase
        try:
            key_a_bin = crypto.load_privatekey(crypto.FILETYPE_PEM, key_a, passphrase=pw)
        except crypto.Error:
            key_a_bin = None
        try:
            key_b_bin = crypto.load_privatekey(crypto.FILETYPE_PEM, key_b, passphrase=pw)
        except crypto.Error:
            key_b_bin = None

        key_a_real = crypto.dump_privatekey(crypto.FILETYPE_PEM, key_a_bin) if key_a_bin else 'decryptErrorA'
        key_b_real = crypto.dump_privatekey(crypto.FILETYPE_PEM, key_b_bin) if key_b_bin else 'decryptErrorB'
    else:
        key_a_real = key_a
        key_b_real = key_b
    return True if key_a_real == key_b_real else False
