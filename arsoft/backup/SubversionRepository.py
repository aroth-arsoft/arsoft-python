#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import sys
import getopt
import os
import subprocess
import arsoft.utils

class SubversionRepository:
    
    def __init__(self, path, verbose=False):
        self.m_repopath = path
        self.m_verbose = verbose

    def log(self, msg):
        if self.m_verbose:
            print(str(msg))

    def create(self):
        return arsoft.utils.runcmd('/usr/bin/svnadmin', ["create", self.m_repopath], verbose=self.m_verbose)
        
    def hotcopy(self, backupdir):
        return arsoft.utils.runcmd('/usr/bin/svnadmin', ["hotcopy", self.m_repopath, backupdir, '--clean-logs'], verbose=self.m_verbose)
        
    def dump(self, bakfile, minrev=None, maxrev=None):

        cmdline_dump = ["/usr/bin/svnadmin", "dump", "-q", self.m_repopath]
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

    def get_latest_revision(self):
        (ret, stdout, stderr) = arsoft.utils.runcmdAndGetData('/usr/bin/svnlook', ["youngest", self.m_repopath], verbose=self.m_verbose)
        if ret == 0 and output is not None and len(output):
            ret = int(output, 10)
        else:
            ret = -1
        return ret
