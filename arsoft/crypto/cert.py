#!/usr/bin/python

import os
from pem import *
from OpenSSL import crypto
from datetime import datetime, timedelta, tzinfo

# Adapted from http://delete.me.uk/2005/03/iso8601.html
ISO8601_REGEX = re.compile(r"(?P<year>[0-9]{4})((?P<month>[0-9]{2})((?P<day>[0-9]{2})"
    r"((?P<hour>[0-9]{2})(?P<minute>[0-9]{2})((?P<second>[0-9]{2})(\.(?P<fraction>[0-9]+))?)?"
    r"(?P<timezone>Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?"
)
TIMEZONE_REGEX = re.compile("(?P<prefix>[+-])(?P<hours>[0-9]{2}).(?P<minutes>[0-9]{2})")

class ParseError(Exception):
    """Raised when there is a problem parsing a date string"""

# Yoinked from python docs
ZERO = timedelta(0)
class Utc(tzinfo):
    """UTC
    
    """
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
UTC = Utc()

class FixedOffset(tzinfo):
    """Fixed offset in hours and minutes from UTC
    
    """
    def __init__(self, offset_hours, offset_minutes, name):
        self.__offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO
    
    def __repr__(self):
        return "<FixedOffset %r>" % self.__name

def parse_timezone(tzstring, default_timezone=UTC):
    """Parses ISO 8601 time zone specs into tzinfo offsets
    
    """
    if tzstring == "Z":
        return default_timezone
    # This isn't strictly correct, but it's common to encounter dates without
    # timezones so I'll assume the default (which defaults to UTC).
    # Addresses issue 4.
    if tzstring is None:
        return default_timezone
    m = TIMEZONE_REGEX.match(tzstring)
    prefix, hours, minutes = m.groups()
    hours, minutes = int(hours), int(minutes)
    if prefix == "-":
        hours = -hours
        minutes = -minutes
    return FixedOffset(hours, minutes, tzstring)

def parse_date(datestring, default_timezone=UTC):
    """Parses ISO 8601 dates into datetime objects
    
    The timezone is parsed from the date string. However it is quite common to
    have dates without a timezone (not strictly correct). In this case the
    default timezone specified in default_timezone is used. This is UTC by
    default.
    """
    if not isinstance(datestring, basestring):
        raise ParseError("Expecting a string %r" % datestring)
    m = ISO8601_REGEX.match(datestring)
    if not m:
        raise ParseError("Unable to parse date string %r" % datestring)
    groups = m.groupdict()
    tz = parse_timezone(groups["timezone"], default_timezone=default_timezone)
    if groups["fraction"] is None:
        groups["fraction"] = 0
    else:
        groups["fraction"] = int(float("0.%s" % groups["fraction"]) * 1e6)
    return datetime(int(groups["year"]), int(groups["month"]), int(groups["day"]),
        int(groups["hour"]), int(groups["minute"]), int(groups["second"]),
        int(groups["fraction"]), tz)

class Certificate(PEMItem):
    def __init__(self, pemitem):
        PEMItem.__init__(self, pemitem.blockindex, pemitem.blocktype, pemitem.blockdata)
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, self.blockdata) 
        
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

    def get_issuer(self):
        return self.cert.get_issuer()
        
    def get_version(self):
        return self.cert.get_version()

    def get_serial_number(self):
        return self.cert.get_serial_number()
        
    def has_expired(self):
        return self.cert.has_expired()

    def get_notBefore(self):
        return parse_date(self.cert.get_notBefore())
        
    def get_notAfter(self):
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
            fobj.write(prefix + "  Hash: " + str(self.getHash()) + '\n')
            fobj.write(prefix + "  Version: " + str(version) + '\n')
            fobj.write(prefix + "  Serial Number: " + str(serial) + '\n')
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

    def add(self, filename):
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
#        if not short:
 #           print("Certificates within " + ','.join(self.m_certificate_filename))

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
