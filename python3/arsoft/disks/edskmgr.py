#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import isRoot, runcmdAndGetData
from arsoft.inifile import IniFile
from arsoft.timestamp import timestamp_from_datetime
from .disk import Drive, Disks
from .scsi import Scsi
from .edskmgr_config import *
import syslog
import sys
import os
import tempfile
import datetime, time

class ExternalDiskManager(object):

    def __init__(self, trigger=None):
        self.verbose = False
        self.noop = False
        self.config = ExternalDiskManagerConfig()
        self._trigger = trigger
        self._private_operation_data = None

        syslog.openlog('edskmgr', logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)
        
    def cleanup(self):
        if self._private_operation_data is not None:
            # only remove the private operation data if we created/own it
            self._remove_private_operation_data()

    def log(self, msg):
        if self.verbose:
            sys.stdout.write(msg)
        syslog.syslog(syslog.LOG_DEBUG, msg)

    def err(self, msg):
        sys.stderr.write(msg)
        syslog.syslog(syslog.LOG_ERR, msg)

    def _get_udev_env(self):
        ret = {}
        for envvar in ['DEVTYPE', 'DEVPATH', 'DEVNAME', 'ACTION', 'ID_FS_LABEL', 'ID_FS_UUID']:
            ret[envvar] = os.environ[envvar] if envvar in os.environ else None
        return ret

    @property
    def hook_dir(self):
        return self.config.hook_dir

    @property
    def config_dir(self):
        return self.config.config_dir
    
    @property
    def trigger(self):
        return self._trigger
    
    @trigger.setter
    def trigger(self, value):
        if value is not None:
            self._trigger = value
            self._save_private_operation_data()

    def checkRoot(self):
        if isRoot():
            ret = True
        elif self.noop:
            ret = True
        else:
            sys.stderr.write("Warning: Not running as root. Currently running as user %s. Some operations may fail.\n" % (os.getlogin()))
            ret = True
        return ret
    
    def _load_private_operation_data(self):
        ret = True
        tempdir = tempfile.gettempdir()
        trigger_file = os.path.join(tempdir, 'edskmgr_operation.private')
        if os.path.exists(trigger_file):
            inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
            inifile.open(trigger_file)
            self._trigger = inifile.get(None, 'Trigger', None)
        else:
            self._trigger = None
            self._private_operation_data = None
        return ret
    
    def _save_private_operation_data(self):
        ret = True
        tempdir = tempfile.gettempdir()
        trigger_file = os.path.join(tempdir, 'edskmgr_operation.private')
        inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
        inifile.open(trigger_file)
        self._private_operation_data = self
        inifile.set(None, 'Trigger', self._trigger)
        ret = inifile.save(trigger_file)
        return ret
    
    def _remove_private_operation_data(self):
        tempdir = tempfile.gettempdir()
        trigger_file = os.path.join(tempdir, 'edskmgr_operation.private')
        if os.path.exists(trigger_file):
            try:
                os.remove(trigger_file)
                ret = True
            except IOError:
                ret = False
        else:
            ret = True
        return ret

    def load_config(self, configdir=None, root_dir=None):
        ret = self.config.open(configdir, root_dir)
        self._load_private_operation_data()
        return ret

    def write_config(self, config_dir=None, root_dir=None):
        return self.config.save(config_dir, root_dir)

    def is_internal_disk(self, diskobj):
        ret = False
        found = False
        if not found:
            for pattern in self.config.internal_disks:
                if diskobj.match(pattern):
                    ret = True
                    found = True
                    break
        if not found:
            for pattern in self.config.external_disks:
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
        return self.config.internal_disks

    @property
    def external_disks(self):
        return self.config.external_disks

    def load_udev_partition(self, devname):
        self.log('loadUDevPartition ' + str(devname))
        #self._loadExternalPartition(devname)
        return False

    def load_udev_disk(self, devname):
        self.log('loadUDevDisk ' + str(devname) + ' - do nothing')
        return True

    def rescan_empty_scsi_hosts(self, only_empty=True):
        if self.noop:
            ret = True
            self.log('rescan empty SCSI hosts successful (noop)\n')
        else:
            scsi_mgr = Scsi()
            ret = scsi_mgr.rescan_hosts(only_empty=only_empty)
            if ret:
                self.log('rescan empty SCSI hosts successful\n')
            else:
                self.err('rescan empty SCSI hosts failed, error %s\n' % (scsi_mgr.last_error))
        return ret
    
    def _remove_disk_impl(self, disk_mgr, scsi_mgr, disk_obj, use_scsi=False):
        if self.is_external_disk(disk_obj):
            ret = True
            self.log('ejecting disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            for child_obj in disk_obj.childs:
                self.log('  eject child %s\n'%(str(child_obj.path)))
                if child_obj.is_mounted:
                    if self.noop:
                        self.log('  unmount %s skipped (noop)\n'%(str(child_obj.path)))
                    elif not child_obj.unmount():
                        self.err('  failed to unmount %s\n'%(str(child_obj.path)))
                        ret = False
                        break
            if ret:
                if use_scsi:
                    devices = scsi_mgr.find_device(syspath=disk_obj.path)
                    if devices:
                        for scsi_disk_obj in devices:
                            if self.noop:
                                self.log('  delete scsi device  %s %s (%s) skipped (noop)\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile)))
                            else:
                                if not scsi_disk_obj.standby():
                                    self.err('  failed to set scsi device %s %s (%s) on standby, error %s\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile), scsi_mgr.last_error))
                                if not scsi_disk_obj.delete():
                                    self.err('  failed to delete scsi device %s %s (%s), error %s\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile), scsi_mgr.last_error))
                                    ret = False
                                else:
                                    self.log('  delete scsi %s %s (%s)\n'%(str(scsi_disk_obj.vendor), str(scsi_disk_obj.model), str(scsi_disk_obj.devfile)))
                else:
                    if not disk_obj.poweroff_and_eject():
                        self.err('  failed to power down and eject %s %s (%s), error %s\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial), disk_mgr.last_error))
                        ret = False
        else:
            self.log('skip internal disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            ret = True
        return ret

    def remove_external_disks(self):
        ret = True
        disk_mgr = Disks()
        scsi_mgr = Scsi()
        for disk_obj in disk_mgr.drives:
            if not self._remove_disk_impl(disk_mgr, scsi_mgr, disk_obj):
                self.err('Failed to remove device %s %s (%s).\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                ret = False
        return ret

    def remove_disks(self, devices):
        ret = True
        disk_mgr = Disks()
        scsi_mgr = Scsi()
        for devname in devices:
            disk_obj = disk_mgr.find_drive_from_user_input(devname)
            if disk_obj:
                if not self._remove_disk_impl(disk_mgr, scsi_mgr, disk_obj):
                    self.err('Failed to remove device %s %s (%s).\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
            else:
                self.err('Given device name %s is not a valid block device.\n'%(devname))
        return ret

    def remove_disk(self, disk_obj):
        ret = True
        disk_mgr = Disks()
        scsi_mgr = Scsi()
        if not self._remove_disk_impl(disk_mgr, scsi_mgr, disk_obj):
            self.err('Failed to remove device %s %s (%s).\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            ret = False
        return ret

    def reset_config(self):
        ret = self.config.reset()
        if ret:
            disk_mgr = Disks()
            for disk_obj in disk_mgr.drives:
                if not self.config.register_disk(disk_obj.disk_name, disk_obj.match_pattern, external=False):
                    self.err('failed to register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
                else:
                    self.log('register disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
        return ret

    def get_disk_for_file(self, path):
        disk_mgr = Disks()
        disk_obj = disk_mgr.find_drive_for_file(path)
        return disk_obj

    def register_disk(self, devices, external=True, tags=[]):
        ret = True
        disk_mgr = Disks()
        for devname in devices:
            disk_obj = disk_mgr.find_drive_from_user_input(devname)
            if disk_obj:
                if not self.config.register_disk(disk_obj.disk_name, disk_obj.match_pattern, external=external, tags=tags):
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
            disk_obj = disk_mgr.find_drive_from_user_input(devname)
            if disk_obj:
                if not self.config.unregister_disk(disk_obj.disk_name, disk_obj.match_pattern, external=external):
                    self.err('failed to unregister disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
                    ret = False
                else:
                    self.log('unregister disk %s %s (%s)\n'%(str(disk_obj.vendor), str(disk_obj.model), str(disk_obj.serial)))
            else:
                self.err('Given device name %s is not a valid block device.\n'%(devname))
        return ret

    def run_hooks(self, command, dev_obj, disk_obj, args=[]):
        ret = True
        hook_args = [ command ]
        if dev_obj:
            hook_args.append(dev_obj.nativepath)
        hook_args.extend(args)

        hook_env = os.environ
        if self._trigger:
            hook_env['EDSKMGR_TRIGGER'] = str(self._trigger)
        if disk_obj:
            hook_env['EDSKMGR_MATCH_PATTERN'] = disk_obj.match_pattern
            hook_env['EDSKMGR_DISK_VENDOR'] = disk_obj.vendor
            hook_env['EDSKMGR_DISK_MODEL'] = disk_obj.model
            hook_env['EDSKMGR_DISK_SERIAL'] = disk_obj.serial
            disk_tags = self.config.get_tags_for_disk(disk_obj.match_pattern)
            hook_env['EDSKMGR_DISK_TAGS'] = ','.join(disk_tags) if disk_tags else ''
            disk_is_internal = self.is_internal_disk(disk_obj)
            hook_env['EDSKMGR_IS_INTERNAL'] = '1' if disk_is_internal else '0'
            hook_env['EDSKMGR_IS_EXTERNAL'] = '0' if disk_is_internal else '1'

        self.log('run_hooks %s from %s args=%s\n'%(command, self.hook_dir, str(args)))
        for item in os.listdir(self.hook_dir):
            fullpath = os.path.abspath(os.path.join(self.hook_dir, item))
            if os.path.isfile(fullpath) and os.access(fullpath, os.X_OK):
                (sts, stdoutdata, stderrdata) = runcmdAndGetData(fullpath, hook_args, env=hook_env)
                if sts != 0:
                    self.err('Script %s failed with %i: %s\n'%(item, sts, stderrdata))
                    ret = False
                else:
                    self.log('Hook %s ok:\n%s\n%s\n'%(item, stdoutdata, stderrdata))
            else:
                self.err('Ignore hook %s because not executable\n'%(item))
        return ret
    
    def udev_hook_initialize(self):
        udev_env = self._get_udev_env()
        action = udev_env['ACTION']
        devpath = udev_env['DEVPATH']
        devtype = udev_env['DEVTYPE']

        disk_mgr = Disks()
        disk_obj = None
        disk_tags = []
        dev_obj = disk_mgr.find_device(devpath=devpath)
        if dev_obj:
            if isinstance(dev_obj, Drive):
                disk_obj = dev_obj
            else:
                disk_obj = disk_mgr.find_drive_for_device(dev_obj)
        if disk_obj:
            disk_tags = self.config.get_tags_for_disk(disk_obj.match_pattern)
        return (disk_obj, dev_obj, disk_tags)

    def udev_action(self):
        udev_env = self._get_udev_env()
        action = udev_env['ACTION']
        devpath = udev_env['DEVPATH']
        devtype = udev_env['DEVTYPE']
        if action == 'add' or action == 'remove':
            if devpath.startswith('/devices/virtual'):
                # DO not run any hooks for virtual devices
                ret = True
            else:
                child_pid = os.fork()
                if child_pid == 0:
                    disk_mgr = Disks()
                    disk_obj = None
                    dev_obj = None
                    num_attempt = 0
                    while dev_obj is None and num_attempt < 10:
                        num_attempt = num_attempt + 1
                        dev_obj = disk_mgr.find_device(devpath=devpath)
                        if dev_obj is None:
                            time.sleep(1.0)
                            disk_mgr.rescan()
                    if dev_obj:
                        if isinstance(dev_obj, Drive):
                            disk_obj = dev_obj
                        else:
                            disk_obj = disk_mgr.find_drive_for_device(dev_obj)
                    if disk_obj:
                        if action == 'add':
                            cmd = 'disk-loaded'
                        else:
                            cmd = 'disk-ejected'
                        ret = self.run_hooks(cmd, dev_obj, disk_obj)
                    else:
                        self.err('Unable to find device %s for %s (%s)\n'%(devpath, action, devtype))
                        ret = False
        else:
            self.err('Unhandled udev action %s for %s (%s)\n'%(action, devpath, devtype))
            ret = False
        return ret
    
    def get_disk_patterns_for_tag(self, tag):
        return self.config.get_disks_by_tag(tag)

    def get_tags_for_disk(self, disk_obj):
        return self.config.get_tags_for_disk(disk_obj.match_pattern)

    def wait_for_disk(self, pattern=None, tag=None, timeout=None, wait_interval=1.0):
        abs_timeout = None
        if not pattern:
            if isinstance(tag, list):
                pattern = []
                for t in tag:
                    patterns_for_tag = self.get_disk_patterns_for_tag(t)
                    pattern.extend(patterns_for_tag)
            else:
                pattern = self.get_disk_patterns_for_tag(tag)
            if len(pattern) == 0:
                # unable to find any patterns for a disk to look for
                return None
        if pattern is None or len(pattern) == 0:
            raise ValueError('Invalid pattern %s' % pattern)
        if timeout is not None:
            if isinstance(timeout, int) or isinstance(timeout, float):
                abs_timeout = time.time()+float(timeout)
            elif isinstance(timeout, datetime.datetime):
                abs_timeout = timestamp_from_datetime(timeout)
            elif isinstance(timeout, datetime.timedelta):
                abs_timeout = time.time()+timeout.total_seconds()
            else:
                raise ValueError('expected int, float, datetime.datetime or datetime.timedelta but cannot handle a %s' % type(timeout))

        disk_mgr = Disks()
        diskobj = disk_mgr.find_drive_by_pattern(pattern)
        if not diskobj:
            if abs_timeout is not None:
                while time.time() < abs_timeout:
                    time.sleep(wait_interval)
                    disk_mgr.rescan()
                    diskobj = disk_mgr.find_drive_by_pattern(pattern)
                    if diskobj:
                        break
        return diskobj
