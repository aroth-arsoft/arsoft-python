#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import isRoot
from .disk import Disk, Disks
from .scsi import Scsi
from .edskmgr_config import *
import syslog
import sys

class ExternalDiskManager(object):

    def __init__(self):
        self._verbose = False
        self._noop = False
        self.config = ExternalDiskManagerConfig()
        self._udev_devtype = None
        self._udev_devname = None
        self._udev_action = None
        self._udev_fs_label = None
        self._udev_fs_uuid = None

        syslog.openlog('edskmgr', logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)

    def log(self, msg):
        if self._verbose:
            sys.stdout.write(msg)
        syslog.syslog(syslog.LOG_DEBUG, msg)

    def err(self, msg):
        sys.stderr.write(msg)
        syslog.syslog(syslog.LOG_ERR, msg)

    @property
    def hook_dir(self):
        return self.config.hook_dir

    @property
    def config_dir(self):
        return self.config.config_dir

    def checkRoot(self):
        if isRoot():
            ret = True
        elif self._noop:
            ret = True
        else:
            sys.stderr.write("Warning: Not running as root. Currently running as user %s. Some operations may fail.\n" % (os.getlogin()))
            ret = True
        return ret

    def load_config(self, configdir=None):
        self.config.open(configdir)

    def write_config(self, config_dir=None):
        return self.config.save(config_dir)

    def is_internal_disk(self, diskobj):
        ret = False
        found = False
        if not found:
            for pattern in self.config.internal_disks.disks:
                if diskobj.match(pattern):
                    ret = True
                    found = True
                    break
        if not found:
            for pattern in self.config.external_disks.disks:
                if diskobj.match(pattern):
                    ret = False
                    found = True
                    break
        if not found:
            # if not found assume it's a internal disk
            ret = True
        else:
            # we found a valid match, so use the value in ret
            pass
        return ret

    def is_external_disk(self, diskobj):
        return not self.is_internal_disk(diskobj)

    @property
    def internal_disks(self):
        return self.config.internal_disks.disks

    @property
    def external_disks(self):
        return self.config.external_disks.disks

    def show_status(self):
        print('Internal disks:')
        for disk in self.config.internal_disks.disks:
            print('  ' + disk)
        print('External disks:')
        for disk in self.config.external_disks.disks:
            print('  ' + disk)

        e = Disks()
        print('Available disks:')
        for disk_obj in e.disks:
            print('  ' + '%s %s (%s)'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            print('    Removeable:  %s'%('yes' if disk_obj.is_removable else 'no'))
            print('    System:      %s'%('yes' if disk_obj.is_system_disk else 'no'))
            print('    Internal:    %s'%('yes' if self.is_internal_disk(disk_obj) else 'no'))

    def load_udev_partition(self, devname):
        if devname is None or len(devname) == 0:
            devname = self._udev_devname
        self.log('loadUDevPartition ' + str(devname))
        #self._loadExternalPartition(devname)
        return False

    def load_udev_disk(self, devname):
        if devname is None or len(devname) == 0:
            devname = self._udev_devname
        self.log('loadUDevDisk ' + str(devname) + ' - do nothing')
        return True

    def rescan_empty_scsi_hosts(self):
        if self._noop:
            ret = True
            self.log('rescan empty SCSI hosts successful (noop)\n')
        else:
            scsi_mgr = Scsi()
            ret = scsi_mgr.rescan_hosts(only_empty=True)
            if ret:
                self.log('rescan empty SCSI hosts successful\n')
            else:
                self.err('rescan empty SCSI hosts failed, error %s\n' % (scsi_mgr.last_error))
        return ret
    
    def remove_external_disks(self):
        ret = True
        disk_mgr = Disks()
        scsi_mgr = Scsi()
        for disk_obj in disk_mgr.disks:
            if self.is_external_disk(disk_obj):
                ret = True
                self.log('ejecting disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                for child_obj in disk_obj.childs:
                    self.log('  eject child %s\n'%(str(child_obj.nativepath)))
                    if child_obj.is_mounted:
                        if not child_obj.unmount():
                            self.err('  failed to unmount %s\n'%(str(child_obj.nativepath)))
                            ret = False
                            break
                if ret:
                    devices = scsi_mgr.find_device(disk_obj.nativepath)
                    if devices:
                        for scsi_disk_obj in devices:
                            if scsi_disk_obj:
                                if not scsi_disk_obj.delete():
                                    self.err('  failed to delete scsi device %s %s (%s), error %s\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile), scsi_mgr.last_error))
                                    ret = False
                                else:
                                    self.log('  delete scsi %s %s (%s)\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile)))
            else:
                self.log('skip internal disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
        return ret

    def reset_config(self):
        ret = self.config.reset()
        if ret:
            disk_mgr = Disks()
            for disk_obj in disk_mgr.disks:
                if not self.config.register_disk(disk_obj.disk_name, disk_obj.match_pattern, external=False):
                    self.err('failed to register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
                else:
                    self.log('register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
        return ret

    def register_disk(self, devices, external=True):
        ret = True
        disk_mgr = Disks()
        for devname in devices:
            disk_obj = disk_mgr.find_disk_from_user_input(devname)
            if disk_obj:
                if not self.config.register_disk(disk_obj.disk_name, disk_obj.match_pattern, external=external):
                    self.err('failed to register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
                else:
                    self.log('register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            else:
                self.err('Given device name %s is not a valid block device.\n'%(devname))
        return ret

    def unregister_disk(self, devices, external=True):
        ret = True
        disk_mgr = Disks()
        for devname in devices:
            disk_obj = disk_mgr.find_disk_from_user_input(devname)
            if disk_obj:
                if not self.config.unregister_disk(disk_obj.disk_name, disk_obj.match_pattern, external=external):
                    self.err('failed to unregister disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
                else:
                    self.log('unregister disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            else:
                self.err('Given device name %s is not a valid block device.\n'%(devname))
        return ret
