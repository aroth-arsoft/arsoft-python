#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os

class MountEntry(object):
    def __init__(self, devicename=None, mountpoint=None, filesystem=None, options=None, freq=0, fpassno=0):
        self._devicename = devicename
        self._mountpoint = mountpoint
        self._filesystem = filesystem
        self._options = [] if options is None else options.split(',')
        self._freq = int(freq) if freq is not None else 0
        self._fpassno = int(fpassno) if fpassno is not None else 0
        pass

    def devicename(self):
        return self._devicename
    def mountpoint(self):
        return self._mountpoint
    def filesystem(self):
        return self._filesystem
    def options(self):
        return self._options
    def hasOption(self, optname):
        return self._options.count(optname) != 0

    def __str__(self):
        return  str(self._devicename) + ' ' + \
                str(self._mountpoint) + ' ' + \
                str(self._filesystem) + ' ' + \
                str(self._options) + ' ' + \
                str(self._freq) + ' ' + \
                str(self._fpassno)
    def isReadOnly(self):
        return True if self._options.count('ro') != 0 else False
    def isReadWrite(self):
        return True if self._options.count('rw') != 0 else False

    def isRoot(self):
        return True if self._mountpoint == '/' else False
    def isRootfs(self):
        return True if self._filesystem == 'rootfs' else False
    def isAutofs(self):
        return True if self._filesystem == 'autofs' else False
    def isProc(self):
        return True if self._filesystem == 'proc' else False
    def isTmpfs(self):
        return True if self._filesystem == 'tmpfs' else False
        
    def isNFS(self):
        return True if self._filesystem == 'nfs' or self._filesystem == 'nfs4' else False
    def isSMB(self):
        return True if self._filesystem == 'smb' else False
    def isCIFS(self):
        return True if self._filesystem == 'cifs' else False

    def isActive(self):
        return os.path.ismount(self._mountpoint)

    def getDiskUsage(self):
        try:
            st = os.statvfs(self._mountpoint)
            free = st.f_bavail * st.f_frsize
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
            ret = (total, used, free)
        except (IOError, OSError) as e:
            ret = None
            pass
        return ret

class MountManager(object):
    def __init__(self):
        self.reload()
    
    def _parseFile(self, filename, entries):
        try:
            mounts = open(filename, 'r')
            for line in mounts:
                if line.startswith('#'):
                    continue
                (devicename, mountpoint, filesystem, options, freq, fpassno) = line.split(' ')
                entry = MountEntry(devicename, mountpoint, filesystem, options, freq, fpassno)
                entries.append(entry)
            mounts.close()
            ret = True
        except (IOError, OSError) as e:
            ret = False
            pass
        return ret

    @staticmethod
    def _getMountpoint(filename):
        ret = None
        last_dirname = filename
        try:
            st = os.stat(filename)
        except (IOError, OSError) as e:
            st = None
            pass
            
        if st:
            last_st = st
            while True:
                parent_dir = os.path.dirname(last_dirname)
                try:
                    st = os.stat(parent_dir)
                except (IOError, OSError) as e:
                    st = None
                    pass
                if st.st_dev != last_st.st_dev or st.st_ino == last_st.st_ino:
                    # parent_dir is the mount point.
                    ret = last_dirname
                    break
                if parent_dir == '/':
                    # stop at root
                    break;
                last_stat = st
                last_dirname = parent_dir
        return ret

    @staticmethod
    def mount(devicename=None, mountpoint=None, options=[]):
        args = []
        if devicename:
            args.append(devicename)
        if mountpoint:
            args.append(mountpoint)
        if len(args) == 0:
            ret = False
        else:
            args.extend(options)
            exitcode = runcmd('/bin/mount', args)
            ret = True if exitcode == 0 else False
        return ret

    @staticmethod
    def umount(devicename=None, mountpoint=None, options=[]):
        args = []
        if devicename:
            args.append(devicename)
        if mountpoint:
            args.append(mountpoint)
        if len(args) == 0:
            ret = False
        else:
            args.extend(options)
            exitcode = runcmd('/bin/umount', args)
            ret = True if exitcode == 0 else False
        return ret

    def reload(self):
        self._active_entries = []
        self._parseFile('/proc/mounts', self._active_entries)
        self._configured_entries = []
        self._parseFile('/etc/fstab', self._configured_entries)

    def __str__(self):
        ret = ''
        for e in self._active_entries:
            ret += str(e) + '\n'
        for e in self._configured_entries:
            ret += str(e) + '\n'
        return ret

    def getRootEntry(self):
        ret = None
        for e in self._active_entries:
            if e.isRoot() and not e.isRootfs():
                ret = e
                break
        return ret
        
    def getEntry(self, mountpoint, active=True):
        ret = None
        if active:
            for e in self._active_entries:
                if e.mountpoint() == mountpoint:
                    ret = e
                    break
        else:
            for e in self._configured_entries:
                if e.mountpoint() == mountpoint:
                    ret = e
                    break
        return ret

    def getEntryForFile(self, filename):
        mp = MountManager._getMountpoint(filename)
        return self.getEntry(mp) if mp is not None else None
        
    def getDeviceNameForFile(self, filename):
        mp = MountManager._getMountpoint(filename)
        if mp:
            entry = self.getEntry(mp)
            if entry:
                ret = entry.devicename()
            else:
                ret = None
        else:
            ret = None
        return ret
        
if __name__ == "__main__":
    mmgr = MountManager()
    print(str(mmgr))
    
    print('Root: ' + str(mmgr.getRootEntry()))
    
    mp = mmgr.getEntryForFile('/tmp/dhclient-script.debug')
    print('mp=' + str(mp))
 
