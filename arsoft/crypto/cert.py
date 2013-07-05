#!/usr/bin/python

import os
import socket, ssl
from urlparse import urlparse
from pem import *
from OpenSSL import crypto
from arsoft.timestamp import parse_date
from arsoft.utils import detect_file_type

class Certificate(PEMItem):
    def __init__(self, pemitem=None, rawitem=None):
        if pemitem:
            PEMItem.__init__(self, pemitem.blockindex, pemitem.blocktype, pemitem.blockdata)
            self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, pemitem.blockdata) 
        elif rawitem:
            tmpcert = crypto.load_certificate(crypto.FILETYPE_ASN1, rawitem)
            blockdata = crypto.dump_certificate(crypto.FILETYPE_PEM, tmpcert)
            PEMItem.__init__(self, 0, 'CERTIFICATE', blockdata)
            self.cert = tmpcert
        else:
            PEMItem.__init__(self, 0, 'CERTIFICATE', None)
            self.cert = None

    def update(self, newcert):
        if isinstance(newcert, Certificate):
            self.cert = newcert.cert
        else:
            self.cert = newcert
        self.blockdata = crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert) 

    def is_same_cert(self, rhs_cert):
        lhs_issuer = self.cert.get_issuer()
        lhs_subject = self.cert.get_subject()
        rhs_issuer = rhs_cert.get_issuer()
        rhs_subject = rhs_cert.get_subject()
        
#        self._printName('  LHS Issuer:  ', lhs_issuer)
#        self._printName('  RHS Issuer:  ', rhs_issuer)
#        self._printName('  LHS Subject: ', lhs_subject)
#        self._printName('  RHS Subject: ', rhs_subject)
        
        return lhs_issuer.hash() == rhs_issuer.hash() and lhs_subject.hash() == rhs_subject.hash()
    
    def expires_later(self, rhs_cert):
        lhs_not_before = self.get_notBefore()
        lhs_not_after = self.get_notAfter()
        rhs_not_before = rhs_cert.get_notBefore()
        rhs_not_after = rhs_cert.get_notAfter()

        print('  LHS Not After:  ', lhs_not_after.ctime())
        print('  RHS Not After:  ', rhs_not_after.ctime())
        print('  LHS Not Before: ', lhs_not_before.ctime())
        print('  RHS Not Before: ', rhs_not_before.ctime())
        return lhs_not_after > rhs_not_after

    def _matchName(self, name, term):
        if term is None or term == 'all':
            ret = True
        else:
            ret = False
            for (key, value) in name.get_components():
                if value.count(term) != 0:
                    ret = True
                    break
        return ret

    def _matchCert(self, term):
        issuer = self.cert.get_issuer()
        subject = self.cert.get_subject()
        return self._matchName(issuer, term) or self._matchName(subject, term)

    def _is_identical_cert(self, rhs_cert):
        return self.is_same_cert(rhs_cert) and self.get_serial_number() == rhs_cert.get_serial_number()
        
    def get_subject(self):
        return self.cert.get_subject()

    @property
    def subject(self):
        return self.cert.get_subject()

    def get_issuer(self):
        return self.cert.get_issuer()

    @property
    def issuer(self):
        return self.cert.get_issuer()

    def get_version(self):
        return self.cert.get_version()

    @property
    def version(self):
        return self.cert.get_version()

    def get_serial_number(self):
        return self.cert.get_serial_number()

    @property
    def serial_number(self):
        return self.cert.get_serial_number()

    def get_pubkey(self):
        return self.cert.get_pubkey()

    @property
    def public_key(self):
        return self.cert.get_pubkey()

    def get_pubkey_bits(self):
        pkey = self.cert.get_pubkey()
        if pkey is not None:
            return pkey.bits()
        else:
            return None

    @property
    def public_key_bits(self):
        pkey = self.cert.get_pubkey()
        if pkey is not None:
            return pkey.bits()
        else:
            return None

    def get_pubkey_type(self):
        pkey = self.cert.get_pubkey()
        if pkey is not None:
            return pkey.type()
        else:
            return None
            
    def get_pubkey_type_str(self):
        pkey = self.cert.get_pubkey()
        if pkey is not None:
            pkeytype = pkey.type()
            if pkey.type() == crypto.TYPE_RSA:
                return 'RSA'
            elif pkey.type() == crypto.TYPE_DSA:
                return 'DSA'
            else:
                return 'Unknown'
        else:
            return 'Unknown'

    def digest(self, digest_name='sha1'):
        return self.cert.digest(digest_name)

    @property
    def has_expired(self):
        return self.cert.has_expired()

    def get_notBefore(self):
        return parse_date(self.cert.get_notBefore())
        
    def get_notAfter(self):
        return parse_date(self.cert.get_notAfter())

    @property
    def issue_date(self):
        return parse_date(self.cert.get_notBefore())

    @property
    def expire_date(self):
        return parse_date(self.cert.get_notAfter())
    
    def _writeName(self, fobj, prefix, name):
        text = ''
        for (key, value) in name.get_components():
            if len(text) != 0:
                text += ', '
            text += key + '=' + value
        fobj.write(prefix + text + '\n')
        
    def _writeNamePretty(self, fobj, label, name, indent=0):
        prefix = ' ' * indent
        
        where = ''
        if name.localityName:
            where = name.localityName
        if name.countryName:
            if len(where) != 0:
                where += ', '
            where += name.countryName
        if name.stateOrProvinceName:
            if len(where) != 0:
                where += ', '
            where += name.stateOrProvinceName
            
        org = ''
        if name.organizationName:
            org = name.organizationName
        if name.organizationalUnitName:
            if len(org) != 0:
                org += ', '
            org += name.organizationalUnitName
        if name.emailAddress:
            if len(org) != 0:
                org += ' '
            org += '(' + name.emailAddress + ')'

        fobj.write(prefix + label + unicode(name.commonName))
        if len(org):
            fobj.write(', ' + org)
        if len(where):
            fobj.write(' at ' + where)
        fobj.write('\n')
    
    def writePretty(self, fobj, indent=0, filename=None, certno=None, short=False):
        issuer = self.cert.get_issuer()
        serial = self.get_serial_number() 
        try:
            signature_algorithm = cert.get_signature_algorithm()
        except:
            signature_algorithm = 'Unknown'
        subject = self.get_subject()
        version = self.get_version()
        not_before = self.get_notBefore()
        not_after = self.get_notAfter()
        has_expired = self.cert.has_expired() 
        num_extension = self.cert.get_extension_count()
        # cert.get_extension(index) 
        
        prefix = ' ' * indent

        if short:
            fobj.write(filename + '\n')
        else:
            if filename:
                if certno:
                    fobj.write(prefix + "Certificate " + filename + " #" + str(certno) + ":\n")
                else:
                    fobj.write(prefix + "Certificate " + filename + ":\n")
            else:
                if certno:
                    fobj.write(prefix + "Certificate #" + str(certno) + ":\n")
                else:
                    fobj.write(prefix + "Certificate:\n")
            fobj.write(prefix + "  Version: " + str(version) + '\n')
            fobj.write(prefix + "  Bits: " + self.get_pubkey_type_str() + '/' + str(self.get_pubkey_bits()) + '\n')
            fobj.write(prefix + "  Hash: " + str(self.getHash()) + '\n')
            fobj.write(prefix + "  Digest MD5: " + str(self.digest('md5')) + '\n')
            fobj.write(prefix + "  Digest SHA1: " + str(self.digest('sha1')) + '\n')
            fobj.write(prefix + ("  Serial Number: %i (0x%X)\n" %(serial, serial)))
            fobj.write(prefix + "  Signature Algorithm: " + str(signature_algorithm) + '\n')
            self._writeNamePretty(fobj, '  Issuer:  ', issuer)
            fobj.write(prefix + "  Validity" + '\n')
            fobj.write(prefix + "    Not Before: " + not_before.ctime() + '\n')
            fobj.write(prefix + "    Not After : " + not_after.ctime() + '\n')
            self._writeNamePretty(fobj, '  Subject: ', subject)
 

class CertificateList:
    def __init__(self):
        self.m_certificates = []
        
    def _getAllCertFilesInDir(self, dirname):
        ret = []
        exclude_dirs = ['.svn', 'CVS', '.git' ]
        cert_file_exts = ['.pem', '.crt' ]
        for direntry in os.listdir(dirname):
            fullname = os.path.join(dirname, direntry)
            if os.path.isdir(fullname):
                if not direntry in exclude_dirs:
                    ret.extend( self._getAllCertFilesInDir(fullname) )
            else:
                (basename, ext) = os.path.splitext(direntry)
                if ext in cert_file_exts:
                    ret.append(fullname)
        return ret
    
    @property
    def empty(self):
        return True if len(self.m_certificates) == 0 else False

    def __getitem__(self, key):
        # if key is of invalid type or value, the list values will raise the error
        return self.m_certificates[key]
    def __setitem__(self, key, value):
        self.m_certificates[key] = value

    def __len__(self):
        return len(self.m_certificates)
    def __iter__(self):
        return iter(self.m_certificates)

    def add(self, filename):
        call_add_file_or_dir = True
        if '://' in filename:
            (scheme, rest) = filename.split('://', 2)
            if scheme == 'file':
                filename = rest
            else:
                call_add_file_or_dir = False
                ret = self.addServer(scheme, filename)
        if call_add_file_or_dir:
            if os.path.isdir(filename):
                ret = self.addDirectory(filename)
            else:
                ret = self.addFile(filename)
        return ret
    
    def addFile(self, filename):
        pemfile = CertificatePEMFile(filename)
        if pemfile.open():
            for cert in pemfile.getCertificates():
                cert_tuple = (filename, cert)
                self.m_certificates.append(cert_tuple)
            ret = True
        else:
            ret = False
        return ret
    
    def addDirectory(self, dirname):
        ret = False
        dir_files = self._getAllCertFilesInDir(dirname)
        
        for file_in_dir in dir_files:
            if self.addFile(file_in_dir):
                ret = True
        return ret

    def addServer(self, scheme, url):
        url_obj = urlparse(url)
        if url_obj.port:
            port_num = url_obj.port
        else:
            port_num = socket.getservbyname(url_obj.scheme)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # require a certificate from the server
            ssl_sock = ssl.wrap_socket(s, cert_reqs=ssl.CERT_NONE)
            ssl_sock.settimeout(30.0)
            #print((url_obj.hostname, port_num))
            ssl_sock.connect((url_obj.hostname, port_num))
            ssl_sock.getpeername()

            cert = Certificate(rawitem=ssl_sock.getpeercert(True))
            cert_tuple = (url, cert)
            print(cert_tuple)
            self.m_certificates.append(cert_tuple)
            # note that closing the SSLSocket will also close the underlying socket
            ssl_sock.close()
            ret = True
        except socket.error as e:
            print(e)
            ret = False
        return ret

    def save(self):
        ret = True
        # find all unique certfiles
        unique_files = {}
        for (certfile, cert) in self.m_certificates:
            if certfile in unique_files:
                unique_files[certfile].append(cert)
            else:
                unique_files[certfile] = [ cert ]
        
        for certfile, certlist in unique_files.iteritems():
            pemfile = PEMFile()
            for cert in certlist:
                pemfile.append(cert)
            ret = pemfile.save(certfile)
        return ret
        
    def write(self, fobj, expired_only=False, valid_only=False, output_number=True, short=False):
        num_certs = 0
        for (certfile, cert) in self.m_certificates:
            if expired_only:
                if cert.has_expired():
                    cert.writePretty(fobj, filename=certfile, certno=num_certs, short=short)
                    num_certs = num_certs + 1
            elif valid_only:
                if not cert.has_expired():
                    cert.writePretty(fobj, filename=certfile, certno=num_certs, short=short)
                    num_certs = num_certs + 1
            else:
                cert.writePretty(fobj, filename=certfile, certno=num_certs, short=short)
                num_certs = num_certs + 1

        if output_number and not short:
            fobj.write("Number of certificates: " + str(num_certs) + "\n")

    def find(self, term):
        ret = []
        for (certfile, cert) in self.m_certificates:
            if self._matchCert(cert, term):
                ret.append( (certfile, cert) )
        return ret
        
    def update(self, rhs):
        ret = 0
        for (certfile, cert) in self.m_certificates:
            for (rhs_certfile, rhs_cert) in rhs.m_certificates:
                if cert.is_same_cert(rhs_cert):
                    if rhs_cert.expires_later(cert):
                        #print(rhs_certfile + ' replaces ' + certfile)
                        cert.update(rhs_cert)
                        ret = ret + 1
        return ret

    def replace(self, term, newcert):
        ret = False
        for (certfile, cert) in self.m_certificates:
            if self._matchCert(cert, term):
                cert.update(newcert)
                ret = True
        return ret
        
class CertificateListFile:
    def __init__(self, filename=None):
        self.m_filename = filename
        self.m_lines = []

    def open(self, filename=None):
        if filename is None:
            filename = self.m_filename

        lineno = 0
        self.m_lines = []
        try:
            f = open(filename, 'r')
            for line in f:
                if line[0] == '#':
                    # it's a comment, so skip this line but keep it for later
                    # (comment, certfile, active)
                    line_obj = (True, line[1:].rstrip(), False)
                elif line[0] == '!':
                    line_obj = (False, line[1:].rstrip(), False)
                else:
                    line_obj = (False, line.rstrip(), True)

                self.m_lines.append(line_obj)
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
            for (comment, certfile, active) in self.m_lines:
                if comment:
                    f.write('#' + certfile + '\n')
                else:
                    if active:
                        f.write(certfile + '\n')
                    else:
                        f.write('!' + certfile + '\n')
            f.close()
            ret = True
        except:
            ret = False
            pass
        return ret

    def enableCertificate(self, cert_filename, enable=True):
        i = 0
        ret = False
        while i < len(self.m_lines):
            (comment, current_cert_filename, active) = self.m_lines[i]
            if current_cert_filename == cert_filename:
                self.m_lines[i] = (comment, cert_filename, enable)
                ret = True
            i = i + 1
        return ret

    def addCertificate(self, cert_filename, enable=True):
        i = 0
        ret = False
        while i < len(self.m_lines):
            (comment, current_cert_filename, active) = self.m_lines[i]
            if current_cert_filename == cert_filename:
                self.m_lines[i] = (comment, cert_filename, enable)
                ret = True
            i = i + 1
        if not ret:
            cert_tuple = (comment, cert_filename, enable)
            self.m_lines.append( cert_tuple )
        return ret

    def removeCertificate(self, cert_filename):
        ret = False
        i = 0
        while i < len(self.m_lines):
            (comment, current_cert_filename, active) = self.m_lines[i]
            if current_cert_filename == cert_filename:
                self.m_lines.pop(i)
                ret = True
            i = i + 1
        return ret
        
class CertificatePEMFile(PEMFile):
    def __init__(self, filename=None):
        PEMFile.__init__(self, filename)
        
    def getCertificates(self):
        ret = []
        i = 0
        while i < len(self.m_blocks):
            pemitem = self.m_blocks[i]
            if pemitem.blocktype == 'CERTIFICATE':
                cert = Certificate(pemitem)
                ret.append( cert )
            i = i + 1
        return ret

    @property
    def certificates(self):
        return self.getCertificates()

class CertificateFile(object):
    def __init__(self, filename=None):
        self.filename = filename
        self.file_type = None
        self._impl = None
        if self.filename is not None:
            self.open()

    def open(self, filename=None):
        if filename is None:
            filename = self.filename

        if self.file_type is None:
            self.file_type = detect_file_type(filename) if filename else None

        if self.file_type == 'PEM certificate':
            self._impl = CertificatePEMFile(self.filename)
            ret = self._impl.open()
        else:
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
    def certificates(self):
        if self._impl:
            return self._impl.certificates
        else:
            return []
    