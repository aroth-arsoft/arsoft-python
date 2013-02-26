#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import dbus
import os.path
import stat

class Disk(object):
    DEVICE_CLASS = 'org.freedesktop.UDisks.Device'
    def __init__(self, path=None):
        self._path = path
        self._device_obj = None
        self._device_props = None

    def _dbus_get_device(self):
        self._device_obj = Disks._dbus_system_bus.get_object("org.freedesktop.UDisks", self._path)
        if self._device_obj is not None:
            self._device_props = dbus.Interface(self._device_obj, dbus.PROPERTIES_IFACE)
        return True if self._device_props is not None else False
        
    def _dbus_get_property(self, property_name):
        if not self._dbus_get_device():
            return None
        ret = self._device_props.Get(Disk.DEVICE_CLASS, property_name)
        return ret

    @property
    def vendor(self):
        return self._dbus_get_property("DriveVendor")

    @property
    def model(self):
        return self._dbus_get_property("DriveModel")

    @property
    def serial(self):
        return self._dbus_get_property("DriveSerial")

    @property
    def devicefile(self):
        return self._dbus_get_property("DeviceFile")

    @property
    def devicefile_presentation(self):
        return self._dbus_get_property("DeviceFilePresentation")

    @property
    def devicefile_by_path(self):
        return self._dbus_get_property("DeviceFileByPath")

    @property
    def devicefile_by_id(self):
        return self._dbus_get_property("DeviceFileById")

    @property
    def nativepath(self):
        return self._dbus_get_property("NativePath")
    
    @property
    def mountpath(self):
        return self._dbus_get_property("DeviceMountPaths")

    @property
    def partitionsize(self):
        return self._dbus_get_property("PartitionSize")
    
    @property
    def is_media_ejectable(self):
        return self._dbus_get_property("DriveIsMediaEjectable")

    @property
    def is_media_available(self):
        return self._dbus_get_property("DeviceIsMediaAvailable")

    @property
    def is_optical_disc(self):
        return self._dbus_get_property("DeviceIsOpticalDisc")

    @property
    def is_readonly(self):
        return self._dbus_get_property("DeviceIsReadOnly")

    @property
    def is_mounted(self):
        return self._dbus_get_property("DeviceIsMounted")

    @property
    def is_drive(self):
        return self._dbus_get_property("DeviceIsDrive")
    
    @property
    def is_removable(self):
        return self._dbus_get_property("DeviceIsRemovable")

    def match(self, pattern):
        # check for valid pattern
        if ':' in pattern:
            key, value = pattern.split(':')
        else:
            # no valid pattern, so treat it like a serial number
            key = 'serial'
            value = pattern
        if key == 'serial':
            ret = True if self.serial == value else False
        elif key == 'vendor':
            ret = True if self.vendor == value else False
        elif key == 'model':
            ret = True if self.model == value else False
        elif key == 'devicefile':
            ret = True if self.devicefile == value else False
        else:
            ret = False
        return ret

    @property
    def disk_name(self):
        return '%s_%s_%s'%(self.vendor,self.model,self.serial)

    @property
    def match_pattern(self):
        return 'vendor:%s,model:%s,serial:%s'%(self.vendor,self.model,self.serial)

    def __str__(self):
        ret = 'vendor=' + str(self.vendor) + ' model=' + str(self.model) +\
            ' serial=' + str(self.serial) +\
            ' mounted=' + ','.join(self.mountpath) +\
            ''
        return ret

class Disks(object):
    _dbus_system_bus = None
    _udisks_manager_obj = None
    _udisks_manager = None

    def __init__(self):
        self._rescan()
        
    def _rescan(self):
        self._list = []
        if not Disks._dbus_connect():
            return False
        for path in Disks._udisks_manager.EnumerateDevices():
            self._list.append(Disk(path))
        ret = True
        return ret

    @staticmethod
    def _dbus_connect():
        if Disks._dbus_system_bus is None:
            Disks._dbus_system_bus = dbus.SystemBus()
            Disks._udisks_manager_obj = Disks._dbus_system_bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
            Disks._udisks_manager = dbus.Interface(Disks._udisks_manager_obj, 'org.freedesktop.UDisks')
        
        return True if Disks._udisks_manager is not None else False

    def find_disk(self, devfile):
        if not Disks._dbus_connect():
            return None
        path = Disks._udisks_manager.FindDeviceByDeviceFile(devfile)
        if path:
            print('got path ' + path)
            ret = Disk(path)
        else:
            ret = None
        return ret
    
    def find_disk_from_user_input(self, devname):
        if os.path.exists(devname):
            # given argument might be a device file
            s = os.stat(devname)
            if stat.S_ISBLK(s.st_mode):
                ret = self.find_disk(devname)
            else:
                ret = None
        else:
            ret = None
        return ret

    def __str__(self):
        ret = ''
        for d in self._list:
            ret = ret + str(d) + "\n"
        return ret
    
    @property
    def drives(self, include_removal=False):
        ret = []
        for d in self._list:
            if d.is_drive:
                add = True
                if include_removal == False and d.is_removable:
                    add = False
                if add:
                    ret.append(d)
        return ret
    
    @property
    def system_drive(self):
        ret = self.root_partition
        for d in self._list:
            if d.is_mounted and '/' in d.mountpath:
                ret = d
        return ret
    
    @property
    def root_partition(self):
        ret = None
        for d in self._list:
            if d.is_mounted and '/' in d.mountpath:
                ret = d
        return ret

if __name__ == '__main__':
    
    e = Disks()
    print('drives:')
    for drive in e.drives:
        print(drive)

    print('system drive:')
    print(e.system_drive)
