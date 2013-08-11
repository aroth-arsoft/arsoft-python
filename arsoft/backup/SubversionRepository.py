#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from BaseRepository import *
import re

class SubversionRepository(BaseRepository):
    
    def __init__(self, path, verbose=False):
        BaseRepository.__init__(self, path, verbose)
        self._is_working_directory = None
        
    def _determine_directory_type(self):
        if self._is_working_directory is None:
            if SubversionRepository.is_working_directory(self._path):
                self._is_working_directory = True
            else:
                self._is_working_directory = False

    @staticmethod
    def is_working_directory(path):
        return True if os.path.isdir(os.path.join(path, '.svn')) else False

    @staticmethod
    def is_repository(path):
        return True if os.path.isfile(os.path.join(path,'format')) else False

    @staticmethod
    def is_svn_url(path):
        if path.startswith('svn://'):
            return True
        elif path.startswith('svn+ssh://'):
            return True
        else:
            return False

    @staticmethod
    def is_valid(path):
        while True:
            if SubversionRepository.is_svn_url(path):
                return True
            if SubversionRepository.is_working_directory(path):
                return True
            elif SubversionRepository.is_repository(path):
                return True
            else:
                (head, tail) = os.path.split(path)
                if head != path:
                    path = head
                else:
                    break
        return False

    def create(self, **kwargs):
        return arsoft.utils.runcmd('/usr/bin/svnadmin', ["create", self._path], verbose=self._verbose)
        
    def hotcopy(self, backupdir):
        return arsoft.utils.runcmd('/usr/bin/svnadmin', ["hotcopy", self._path, backupdir, '--clean-logs'], verbose=self._verbose)
        
    def dump(self, bakfile, minrev=None, maxrev=None):

        cmdline_dump = ["/usr/bin/svnadmin", "dump", "-q", self._path]
        if minrev is not None and maxrev is not None:
            cmdline_dump.append("--incremental")
            cmdline_dump.append("--revision")
            cmdline_dump.append(str(minrev) + ":" + str(maxrev))
        cmdline_bzip2 = ["/bin/bzip2"]

        try:
            bakhandle = open(bakfile, 'wb')

            try:
                self.log("cmdline_dump " + str(cmdline_dump))
                pdump = subprocess.Popen(cmdline_dump, stdout=subprocess.PIPE)
            except OSError, e:
                pdump = None
                print >>sys.stderr, "Execution failed:", e

            try:
                self.log("cmdline_bzip2 " + str(cmdline_bzip2))
                pbzip2 = subprocess.Popen(cmdline_bzip2, stdin=pdump.stdout, stdout=bakhandle)
            except OSError, e:
                pbzip2 = None
                print >>sys.stderr, "Execution failed:", e

            if pdump is not None and pbzip2 is not None:
                pbzip2.wait()
                ret = pbzip2.returncode
            else:
                ret = -1

            bakhandle.close()

        except OSError, e:
            ret = -1
            print >>sys.stderr, "Failed to open " + bakfile, e

        return ret

    def restoredump(self, filelist, dumpfile):
        cmdline_dump = ["/bin/cat"]
        for f in filelist:
            cmdline_dump.append(f)
        cmdline_bunzip2 = ["/bin/bunzip2"]

        try:
            dumphandle = open(dumpfile, 'wb')

            try:
                print "cmdline_dump " + str(cmdline_dump)
                pdump = subprocess.Popen(cmdline_dump, stdout=subprocess.PIPE)
            except OSError, e:
                pdump = None
                print >>sys.stderr, "Execution failed:", e

            try:
                self.log("cmdline_bzip2 " + str(cmdline_bunzip2))
                pbunzip2 = subprocess.Popen(cmdline_bunzip2, stdin=pdump.stdout, stdout=dumphandle)
            except OSError, e:
                pbunzip2 = None
                print >>sys.stderr, "Execution failed:", e

            if pdump is not None and pbunzip2 is not None:
                pbunzip2.wait()
                ret = pbunzip2.returncode
            else:
                ret = -1

            dumphandle.close()

        except OSError, e:
            ret = -1
            print >>sys.stderr, "Failed to open " + bakfile, e

        return ret
        
    def load(dumpfile, repo):

        cmdline = ["/usr/bin/svnadmin", "load", "-q", repo]
        self.log("cmdline " + str(cmdline))
        try:
            dumphandle = open(dumpfile, 'rb')
            try:
                load = subprocess.Popen(cmdline, stdin=dumphandle, stdout=subprocess.PIPE)
            except OSError, e:
                load = None
                print >>sys.stderr, "Execution failed:", e
                
            if load is not None:
                load.wait()
                ret = load.returncode
            else:
                ret = -1

            dumphandle.close()
        except OSError, e:
            ret = -1
            print >>sys.stderr, "Failed to open " + dumpfile, e

        return ret
    
    def _get_current_revision_from_repository(self):
        (ret, stdout, stderr) = arsoft.utils.runcmdAndGetData('/usr/bin/svnlook', ['youngest', self._path], verbose=self._verbose)
        if ret == 0 and stdout is not None and len(stdout):
            ret = int(stdout, 10)
        else:
            ret = None
        return ret

    def _get_current_revision_from_working_directory(self):
        (ret, stdout, stderr) = arsoft.utils.runcmdAndGetData('/usr/bin/svn', ['info', self._path], verbose=self._verbose)
        if ret == 0 and stdout is not None and len(stdout):
            ret = stdout.find('Revision:')
            r = re.compile(r'Revision:\s+(?P<rev>[0-9]+)')
            mo = r.search(stdout)
            if mo:
                ret = int(mo.group('rev'))
            else:
                ret = None
        else:
            ret = None
        return ret

    def get_current_revision(self):
        self._determine_directory_type()
        if self._is_working_directory:
            return self._get_current_revision_from_working_directory()
        else:
            return self._get_current_revision_from_repository()
