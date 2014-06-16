#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import sys
from arsoft.zipfileutils import ZipFileEx
import arsoft.crypto
from arsoft.sshutils import *
from OpenSSL import crypto
from configfile import ConfigFile
from systemconfig import SystemConfig
import arsoft.utils
import zipfile
import StringIO

class ZippedConfigFile(object):

    def __init__(self, filename=None, mode='r'):
        self.filename = filename
        self.mode = mode
        self._zip = None
        self._config_file_info = None
        self.last_error = None

    def __str__(self):
        if self._zip:
            return str(self.__class__.__name__) + '(%s;%s)' % (self.filename, self.name)
        else:
            return str(self.__class__.__name__) + '(%s)' % (self.filename)

    def _ensure_open(self):
        if self._zip is None:
            ret = self.open()
        else:
            ret = True
        return ret

    def open(self, filename=None, mode=None):
        if filename is None:
            filename = self.filename
        if mode is None:
            mode = self.mode

        try:
            self._zip = ZipFileEx(filename, mode)
        except zipfile.BadZipfile as e:
            self.last_error = e
            self._zip = None
        except IOError as e:
            self.last_error = e
            self._zip = None
        ret = True if self._zip else False
        return ret

    @staticmethod
    def is_zip_config_file(filename, mode='r'):
        try:
            fobj = ZipFileEx(filename, mode)
            if fobj:
                config_file_info = None
                fileinfolist = fobj.infolist()
                for fileinfo in fileinfolist:
                    (basename, ext) = os.path.splitext(fileinfo.filename)
                    if ext == '.ovpn' or ext == '.conf':
                        config_file_info = fileinfo
                        break
                ret = True if config_file_info else False
                fobj.close()
            else:
                ret = False
        except zipfile.BadZipfile as e:
            ret = False
        return ret

    @staticmethod
    def _create_add_file_to_zip(zipfile_fobj, cfgfile, file_to_add, arcname=None):
        if cfgfile.config_directory:
            source_file = os.path.join(cfgfile.config_directory, file_to_add)
        else:
            source_file = file_to_add
        if os.path.isfile(source_file):
            zipfile_fobj.write(source_file, arcname if arcname else file_to_add)
            ret = True
            error = None
        else:
            ret = False
            error = 'File %s does not exist' %(source_file)
        return (ret, error)

    @staticmethod
    def _create_add_key_file_to_zip(zipfile_fobj, cfgfile, file_to_add, key_passphrase, arcname=None):
        if cfgfile.config_directory:
            source_file = os.path.join(cfgfile.config_directory, file_to_add)
        else:
            source_file = file_to_add
        if os.path.isfile(source_file):
            org_keyfile = arsoft.crypto.KeyPEMFile(source_file)
            
            ret = org_keyfile.open()
            if ret:
                zip_keyfile_stream = StringIO.StringIO()
                ret = org_keyfile.export(zip_keyfile_stream, key_passphrase)
                if ret:
                    data = zip_keyfile_stream.getvalue()
                    zipfile_fobj.writestr(arcname if arcname else file_to_add, data)
                error = None
        else:
            ret = False
            error = 'File %s does not exist' %(source_file)
        return (ret, error)

    @staticmethod
    def create(cfgfile, output_file, key_passphrase=None):
        zip_cfgfile = cfgfile.clone()
        zip_ostype = cfgfile.ostype
        try:
            fobj = ZipFileEx(output_file, 'w')
            if fobj:
                ret = True
                if zip_ostype == 'windows' or zip_ostype == 'macosx':
                    # create a flat zip file
                    zip_private_directory = ''
                else:
                    zip_private_directory = cfgfile.suggested_private_directory + '/'

                if ret and cfgfile.cert_filename:
                    ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.cert_filename, zip_private_directory + 'cert.pem')
                    if ret:
                        zip_cfgfile.cert_filename = zip_private_directory + 'cert.pem'
                if ret and cfgfile.key_filename:
                    if key_passphrase:
                        ret, error = ZippedConfigFile._create_add_key_file_to_zip(fobj, cfgfile, cfgfile.key_filename, key_passphrase, zip_private_directory + 'key.pem')
                    else:
                        ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.key_filename, zip_private_directory + 'key.pem')
                    if ret:
                        zip_cfgfile.key_filename = zip_private_directory + 'key.pem'
                if ret and cfgfile.ca_filename:
                    ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.ca_filename, zip_private_directory + 'ca.pem')
                    if ret:
                        zip_cfgfile.ca_filename = zip_private_directory + 'ca.pem'
                if ret and cfgfile.dh_filename:
                    ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.dh_filename, zip_private_directory + 'dh.pem')
                    if ret:
                        zip_cfgfile.dh_filename = zip_private_directory + 'dh.pem'
                if ret and cfgfile.crl_filename:
                    ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.crl_filename, zip_private_directory + 'crl.pem')
                    if ret:
                        zip_cfgfile.crl_filename = zip_private_directory + 'crl.pem'
                if ret and cfgfile.auth_user_pass_file:
                    ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, cfgfile.crl_filename, zip_private_directory + 'auth_pass')
                    if ret:
                        zip_cfgfile.auth_user_pass_file = zip_private_directory + 'auth_pass'
                if ret and cfgfile.client_config_directory:
                    #print('ccd dir %s' % (cfgfile.client_config_directory))
                    zip_cfgfile.client_config_directory = zip_private_directory + 'ccd'
                    for (client_name, client_config_file) in cfgfile.client_config_files.iteritems():
                        #print('add %s as %s' % (client_config_file, client_name))
                        ret, error = ZippedConfigFile._create_add_file_to_zip(fobj, cfgfile, client_config_file.filename, zip_private_directory + 'ccd/' + client_name)
                        if not ret:
                            break
                if ret:
                    zip_cfgfile.name = cfgfile.name
                    zip_cfgfile_stream = StringIO.StringIO()
                    ret = zip_cfgfile.save(zip_cfgfile_stream)
                    if ret:
                        fobj.writestr(zip_cfgfile.suggested_filename, zip_cfgfile_stream.getvalue())
                fobj.close()
                output_zip = ZippedConfigFile(output_file)
                if not ret:
                    if hasattr(output_file, 'write'):
                        os.remove(output_file.name)
                    else:
                        os.remove(output_file)
                    output_zip.last_error = error
                ret = output_zip
            else:
                ret = None
        except zipfile.BadZipfile as e:
            ret = None
        except IOError as e:
            ret = None
        return ret
        

    @property
    def valid(self):
        ret = self._find_config_file()
        return ret

    def close(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None
        self._config_file_info = None
    
    def _find_config_file(self):
        if self._config_file_info is None:
            if self._ensure_open():
                fileinfolist = self._zip.infolist()
                for fileinfo in fileinfolist:
                    (basename, ext) = os.path.splitext(fileinfo.filename)
                    if ext == '.ovpn' or ext == '.conf':
                        self._config_file_info = fileinfo
                        break
        return True if self._config_file_info is not None else False
    
    def _find_file(self, filename):
        ret = None
        if self._ensure_open():
            fileinfolist = self._zip.infolist()
            for fileinfo in fileinfolist:
                if fileinfo.filename == filename:
                    ret = fileinfo
                    break
        return ret

    @property
    def name(self):
        cfgfile = self.config_file
        if cfgfile is not None:
            return cfgfile.name
        else:
            return None

    @property
    def config_filename(self):
        self._find_config_file()
        return self._config_file_info.filename if self._config_file_info else None

    @property
    def config_file(self):
        self._find_config_file()
        fp = self._zip.open(self._config_file_info.filename, self.mode) if self._config_file_info else None
        ret = ConfigFile(fp, zipfile=self) if fp else None
        return ret
    
    def get_files_in_directory(self, dirname):
        ret = []
        fileinfolist = self._zip.infolist()
        for fileinfo in fileinfolist:
            if fileinfo.filename.startswith(dirname):
                ret.append(fileinfo.filename)
        return ret
    
    def extractall(self, target_directory):
        if self._ensure_open():
            self._zip.extractall(target_directory)
            ret = True
        else:
            ret = False
        return ret

    def __getitem__(self, name):
        fileinfo = self._find_file(name)
        return self._zip.open(fileinfo.filename, self.mode) if fileinfo else None
    
    def __iter__(self):
        if self._ensure_open():
            return iter(self._zip)
        else:
            return None
        
    def extract(self, name, target_directory, target_name=None):
        #print('extract %s to %s' %(name, target_directory))
        if self._ensure_open():
            if target_name is None:
                self._zip.extract(name, target_directory)
                ret = True
            else:
                dstname = os.path.join(target_directory, target_name)
                fileinfo = self._find_file(name)
                if fileinfo:
                    fsrc = self._zip.open(fileinfo.filename, 'r')
                    fdst = open(dstname, 'w')
                    buf_length = 4096
                    while 1:
                        buf = fsrc.read(buf_length)
                        if not buf:
                            break
                        fdst.write(buf)
                    fsrc.close()
                    fdst.close()
                    ret = True
                else:
                    ret = False
        else:
            ret = False
        return ret

    def install(self, autoStart=True, config_directory=None, root_directory=None):
        if config_directory is None:
            config_directory = '/etc/openvpn'
        if root_directory is None:
            target_config_directory = config_directory
        else:
            target_config_directory = root_directory + config_directory

        cfgfile = self.config_file
        ret = True if cfgfile else False
        if ret:
            if not os.path.isdir(target_config_directory):
                try:
                    os.makedirs(target_config_directory)
                    ret = True
                except IOError, OSError:
                    ret = False
        if ret:
            private_config_directory = os.path.join(target_config_directory, cfgfile.suggested_private_directory)
            if not os.path.isdir(private_config_directory):
                try:
                    os.makedirs(private_config_directory)
                    ret = True
                except IOError, OSError:
                    ret = False
        if ret and cfgfile.cert_filename:
            ret = self.extract(cfgfile.cert_filename, private_config_directory, 'cert.pem')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'cert.pem'), target_config_directory)
                cfgfile.cert_filename = new
        if ret and cfgfile.key_filename:
            ret = self.extract(cfgfile.key_filename, private_config_directory, 'key.pem')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'key.pem'), target_config_directory)
                cfgfile.key_filename = new
        if ret and cfgfile.ca_filename:
            ret = self.extract(cfgfile.ca_filename, private_config_directory, 'ca.pem')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'ca.pem'), target_config_directory)
                cfgfile.ca_filename = new
        if ret and cfgfile.dh_filename:
            ret = self.extract(cfgfile.dh_filename, private_config_directory, 'dh.pem')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'dh.pem'), target_config_directory)
                cfgfile.dh_filename = new
        if ret and cfgfile.crl_filename:
            ret = self.extract(cfgfile.crl_filename, private_config_directory, 'crl.pem')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'crl.pem'), target_config_directory)
                cfgfile.crl_filename = new
        if ret and cfgfile.auth_user_pass_file:
            ret = self.extract(cfgfile.crl_filename, private_config_directory, 'auth_pass')
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'auth_pass'), target_config_directory)
                cfgfile.auth_user_pass_file = new
        if ret and cfgfile.client_config_directory:
            private_config_directory_ccd = os.path.join(private_config_directory, 'ccd')
            if not os.path.isdir(private_config_directory_ccd):
                try:
                    os.makedirs(private_config_directory_ccd)
                    ret = True
                except IOError, OSError:
                    ret = False
            if ret:
                for (client_name, client_config_file) in cfgfile.client_config_files.iteritems():
                    ret = self.extract(client_config_file.filename, private_config_directory_ccd, client_name)
                    if not ret:
                        break
            if ret:
                new = os.path.relpath(os.path.join(private_config_directory,'ccd'), target_config_directory)
                cfgfile.client_config_directory = new
        if ret:
            cfgfile.status_file = cfgfile.suggested_status_file
            cfgfile.status_version = cfgfile.suggested_status_version
            cfgfile.management = cfgfile.suggested_management
        if ret:
            target_config_file = os.path.join(target_config_directory, cfgfile.suggested_filename)
            ret = cfgfile.save(target_config_file)
            if not ret:
                self.last_error = cfgfile.last_error

        if ret:
            syscfg = SystemConfig(root_directory=root_directory)
            vpnname, ext = os.path.splitext(cfgfile.suggested_filename)
            new_autostart = syscfg.autostart
            if autoStart:
                new_autostart.add(vpnname)
            else:
                new_autostart.remove(vpnname)
            syscfg.autostart = new_autostart
            ret = syscfg.save()
        return ret

    def ssh_install(self, target_hostname, username=None, keyfile=None, stdout=None, stderr=None, 
                    outputStdErr=False, outputStdOut=False, allocateTerminal=False, x11Forwarding=False,
                    cwd=None, env=None,
                    verbose=False):
        try:
            inputfile = open(self.filename, 'r')
        except IOError as e:
            self.last_error = e
            inputfile = None
        if inputfile:
            # copy zip file to target host as stdin file
            commandline = '/usr/sbin/openvpn-admin --install -'

            (sts, stdout, stderr) = ssh_runcmdAndGetData(target_hostname, commandline=commandline, script=None, 
                                                     outputStdErr=outputStdErr, outputStdOut=outputStdOut, stdin=inputfile, stdout=stdout, stderr=stderr, cwd=cwd, env=env,
                                                     allocateTerminal=allocateTerminal, x11Forwarding=x11Forwarding,
                                                     keyfile=keyfile, username=username, verbose=verbose)
            sts = 0
            ret = True if sts == 0 else False
            inputfile.close()
        else:
            ret = False
        return ret
    
    @staticmethod
    class zip_config_compare_functor(object):
        def __init__(self, key_passphrase):
            self.key_passphrase = key_passphrase

        def __call__(self, selfzip, selfinfo, otherzip, otherinfo):
            ret = True
            if selfinfo.CRC != otherinfo.CRC:
                if os.path.basename(selfinfo.filename) == 'key.pem':
                    selffp = selfzip.open(selfinfo)
                    otherfp = otherzip.open(otherinfo)

                    selfcontent = selffp.read()
                    othercontent = otherfp.read()
                    selffp.close()
                    otherfp.close()

                    ret = arsoft.crypto.compare_pem_key(selfcontent, othercontent, passphrase=self.key_passphrase)
                else:
                    ret = False

            return ret
    
    def compare(self, otherzip, key_passphrase=None):
        if isinstance(otherzip, ZippedConfigFile):
            real_otherzip = otherzip._zip
        elif isinstance(otherzip, str):
            try:
                real_otherzip = ZipFileEx(otherzip, 'r')
            except zipfile.BadZipfile as e:
                self.last_error = e
                real_otherzip = None
            except IOError as e:
                self.last_error = e
                real_otherzip = None
        else:
            real_otherzip = otherzip
        self._ensure_open()
        if self._zip is None:
            return True if real_otherzip is None else False
        else:
            cmpfunc = ZippedConfigFile.zip_config_compare_functor(key_passphrase)
            return self._zip.compare(real_otherzip, date_time=False, content=True, compare_functor=cmpfunc)

if __name__ == '__main__':
    c = ZippedConfigFile(sys.argv[1])

    print(c)
    print(c.config_file)
    print(c.config_file.ca_file)
    print(c[c.config_file.ca_file])
    print(iter(c))
    for f in iter(c):
        print(f.name)
