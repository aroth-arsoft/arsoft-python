#!/usr/bin/python

import sys
import re
import os
import subprocess
import hashlib

class BackupDirectory:
    hash_buffer_size = 256 * 1024
    
    def __init__(self, path, name=None, prefix=None, verbose=False, archivetype='bz2', hashtype='md5'):
        self.m_path = path
        if name is None:
            self.m_name = os.path.basename(path)
        else:
            self.m_name = name
        self.m_prefix = prefix
        self.m_archivetype = archivetype
        self.m_hashtype = hashtype
        self.m_verbose = verbose
        if self.m_prefix:
            re_string = "^" + re.escape(self.m_prefix) + "\_" + re.escape(self.m_name)
        else:
            re_string = "^" + re.escape(self.m_name)
        re_string = re_string + "\_rev\_(?P<rev_from>[0-9]+)\_(?P<rev_to>[0-9]+)\."
        self.m_regexp = re.compile(re_string + re.escape(self.m_archivetype) + "$")
        self.m_regexp_hash = re.compile(re_string + re.escape(self.m_hashtype) + "$")

    def log(self, msg):
        if self.m_verbose:
            print(str(msg))
            
    ######################################################################
    # Helper functions
    @staticmethod
    def backup_file_comparator(a, b):
        a_rev_from = a[1]
        b_rev_from = b[1]
        if (a_rev_from < b_rev_from):
            return -1
        elif (a_rev_from > b_rev_from):
            return 1
        else:
            a_rev_to = a[2]
            b_rev_to = b[2]
            if (a_rev_to < b_rev_to):
                return -1
            else:
                return 1

    @staticmethod
    def _removeFile(filename):
        try:
            os.remove(filename)
            ret = True
        except:
            ret = False
        return ret

    @staticmethod
    def sumfile(fobj):
        '''Returns an md5 hash for an object with read() method.'''
        m = hashlib.md5()
        while True:
            d = fobj.read(BackupDirectory.hash_buffer_size)
            if not d:
                break
            m.update(d)
        return m.hexdigest()

    @staticmethod
    def md5sum(fname):
        '''Returns an md5 hash for file fname, or stdin if fname is "-".'''
        if fname == '-':
            ret = sumfile(sys.stdin)
        else:
            try:
                f = file(fname, 'rb')
            except:
                return 'Failed to open file'
            ret = BackupDirectory.sumfile(f)
            f.close()
        return ret

    @staticmethod
    def generate_hash_file(sourcefile, hashfile):
        hashsum = BackupDirectory.md5sum(sourcefile)
        try:
            h = open(hashfile, 'w')
            h.write(hashsum)
            h.close()
            ret = True
        except OSError, e:
            ret = False
        return ret
        
    @staticmethod
    def verify_hash_file(sourcefile, hashfile):
       
        try:
            h = open(hashfile, 'r')
            precalculated_hash = h.read()
            h.close()
        except:
            precalculated_hash = None
        
        if precalculated_hash is not None:
            newcalculated_hash = BackupDirectory.md5sum(sourcefile)
            
            if newcalculated_hash == precalculated_hash:
                ret = True
            else:
                ret = False
        else:
            ret = False
        return ret
        

    def _get_hash_filename(self, filename):
        (path, ext) = os.path.splitext(filename)
        hashfilename = path + '.' + self.m_hashtype
        return hashfilename
                
    def listFiles(self):
        ret = []
        directory_list = os.listdir(self.m_path)
        for f in directory_list:
            match = self.m_regexp.search(f)
            if match is not None:
                hashfilename = self._get_hash_filename(f)
                if not os.path.exists( os.path.join(self.m_path, hashfilename) ):
                    hashfilename = None
                rev_from = int(match.group('rev_from'))
                rev_to = int(match.group('rev_to'))
                elem = (f, hashfilename, rev_from, rev_to)
                ret.append(elem)
        ret.sort(BackupDirectory.backup_file_comparator)
        return ret
        
    def missingFiles(self):
        ret = []
        filelist = self.listFiles()
        num_files = len(filelist)
        if num_files:
            rev_last = -1
            #print(filelist)
            for (filename, hashfilename, rev_from, rev_to) in filelist:
                if rev_from <= rev_last + 1:
                    if rev_to > rev_last:
                        rev_last = rev_to
                else:
                    ret.append( (rev_last + 1, rev_from) )
        return ret
        
    def bestFiles(self):
        ret = []
        filelist = self.listFiles()
        num_files = len(filelist)
        num_ret = 0
        if num_files:
            rev_last = -1
            rev_last_insert_from = -1
            rev_last_insert_to = -1
            #print(filelist)
            for (filename, hashfilename, rev_from, rev_to) in filelist:
                if rev_from <= rev_last + 1:
                    if rev_to > rev_last:
                        rev_last = rev_to
                        if rev_from > rev_last_insert_from:
                            ret.append( (filename, hashfilename, rev_from, rev_to) )
                            num_ret = num_ret + 1
                        else:
                            ret[num_ret - 1] = (filename, hashfilename, rev_from, rev_to)
                        rev_last_insert_from = rev_from
                        rev_last_insert_to = rev_to
        return ret
        
    def getObsoleteFiles(self):
        filelist = self.listFiles()
        required_filelist = self.bestFiles()
        ret = []
        for (filename, hashfilename, rev_from, rev_to) in filelist:
            required = False
            for (req_filename, _req_hashfilename, _a, _b) in required_filelist:    
                if req_filename == filename:
                    required = True
                    break
            if not required:
                ret.append( (filename, hashfilename) )
        return ret
        
    def removeObsoleteFiles(self):
        delete_list = self.getObsoleteFiles()
        for (filename, hashfilename) in delete_list:
            filename_full = os.path.join(self.m_path, filename)
            hashfilename_full = os.path.join(self.m_path, hashfilename)
            if BackupDirectory._removeFile(filename_full):
                print('deleted ' + str(filename))
                BackupDirectory._removeFile(hashfilename_full)
            else:
                print('failed to delete ' + str(filename))

    def get_latest_revision(self):
        filelist = self.listFiles()
        num_files = len(filelist)
        if num_files:
            (latest_filename, latest_hashfilename, latest_from, latest_to) = filelist[num_files - 1]
            (oldest_filename, oldest_hashfilename, oldest_from, oldest_to) = filelist[0]
            ret = (latest_filename, latest_hashfilename, oldest_from, latest_to)
        else:
            ret = None
        return ret
        
    def verifyFiles(self):
        ret = []
        # only verify the best files
        filelist = self.bestFiles()
        for (filename, hashfilename, rev_from, rev_to) in filelist:
            if hashfilename is not None:
                filename_full = os.path.join(self.m_path, filename)
                hashfilename_full = os.path.join(self.m_path, hashfilename)
                if not BackupDirectory.verify_hash_file(filename_full, hashfilename_full):
                    ret.append( (filename, hashfilename, rev_from, rev_to) )
            else:
                self.log('missing hash for ' + filename)
                ret.append( (filename, hashfilename, rev_from, rev_to) )
        return ret

    def get_filename(self, minrev=None, maxrev=None):
        
        if self.m_prefix is not None:
            filename = self.m_prefix + self.m_name
        else:
            filename = self.m_name
        if minrev is not None and maxrev is not None:
            filename = filename + "_rev_" + str(minrev) + "_" + str(maxrev)

        ret = os.path.join(self.m_path, filename + "." + self.m_archivetype)
        return ret
        
    def get_filenameAndHash(self, minrev=None, maxrev=None):
        
        if self.m_prefix is not None:
            filename = self.m_prefix + '_' + self.m_name
        else:
            filename = self.m_name
        if minrev is not None and maxrev is not None:
            filename = filename + "_rev_" + str(minrev) + "_" + str(maxrev)
        
        ret = os.path.join(self.m_path, filename + "." + self.m_archivetype)
        ret_hash = os.path.join(self.m_path, filename + "." + self.m_hashtype)
            
        return (ret, ret_hash)
        
    def hashFilename(self, sourcefile, hashfile):
        BackupDirectory.generate_hash_file(sourcefile, hashfile)

    def sync_remote(self, remote_site, remote_key=None):
        
        # use SSH without X11 forwarding
        rsync_rsh = '/usr/bin/ssh -x'
        if remote_key:
            rsync_rsh = rsync_rsh + ' -i ' + remote_key
            
        srcdir = os.path.normpath(self.m_path) + '/'
        remote_site_len = len(remote_site)
        destdir = remote_site
        if destdir[remote_site_len - 1] != '/':
            destdir = destdir + '/'
            
        cmdline = ['/usr/bin/rsync', '-z', '-r', '-a', '--delete', '-e', rsync_rsh, srcdir, destdir]
        
        try:
            self.log("sync_remote cmdline " + str(cmdline))
            p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if p:
                (stdoutdata, stderrdata) = p.communicate()
                ret = p.returncode
            else:
                ret = -1
                stdoutdata = None
                stderrdata = None
        except OSError, e:
            print >>sys.stderr, "Execution failed:", e
            ret = -1
            stdoutdata = None
            stderrdata = None
        return (ret, stdoutdata, stderrdata)
