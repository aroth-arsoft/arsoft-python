#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import dbus
import os.path
import stat

class Device(object):
    DEVICE_CLASS = 'org.freedesktop.UDisks.Device'
    def __init__(self, mgr, path, device_obj, device_props):
        self._mgr = mgr
        self._path = path
        self._device_obj = device_obj
        self._device_props = device_props

    @property
    def path(self):
        return self._path

    @property
    def id_uuid(self):
        return Disks._get_device_property(self._device_props, "IdUuid")

    @property
    def id_label(self):
        return Disks._get_device_property(self._device_props, "IdLabel")

    @property
    def id_type(self):
        return Disks._get_device_property(self._device_props, "IdType")

    @property
    def id_usage(self):
        return Disks._get_device_property(self._device_props, "IdUsage")

    @property
    def devicefile(self):
        return Disks._get_device_property(self._device_props, "DeviceFile")

    @property
    def devicefile_presentation(self):
        return Disks._get_device_property(self._device_props, "DeviceFilePresentation")

    @property
    def devicefile_by_path(self):
        return Disks._get_device_property(self._device_props, "DeviceFileByPath")

    @property
    def devicefile_by_id(self):
        return Disks._get_device_property(self._device_props, "DeviceFileById")

    @property
    def nativepath(self):
        return Disks._get_device_property(self._device_props, "NativePath")

    @property
    def mountpath(self):
        return Disks._get_device_property(self._device_props, "DeviceMountPaths")

    @property
    def is_media_ejectable(self):
        return Disks._get_device_property(self._device_props, "DriveIsMediaEjectable")

    @property
    def is_media_available(self):
        return Disks._get_device_property(self._device_props, "DeviceIsMediaAvailable")

    @property
    def is_optical_disc(self):
        return Disks._get_device_property(self._device_props, "DeviceIsOpticalDisc")

    @property
    def is_readonly(self):
        return Disks._get_device_property(self._device_props, "DeviceIsReadOnly")

    @property
    def is_mounted(self):
        return Disks._get_device_property(self._device_props, "DeviceIsMounted")

    @property
    def is_drive(self):
        return Disks._get_device_property(self._device_props, "DeviceIsDrive")
    
    @property
    def is_removable(self):
        return Disks._get_device_property(self._device_props, "DeviceIsRemovable")

    def __repr__(self):
        return str(type(self)) + '[' + self._path + ']'

    def __str__(self):
        ret = 'nativepath=' + str(self.nativepath) +\
            ''
        return ret
    
class Disk(Device):
    def __init__(self, mgr, path, device_obj, device_props):
        super(Disk, self).__init__(mgr, path, device_obj, device_props)

    @property
    def vendor(self):
        return Disks._get_device_property(self._device_props, "DriveVendor")

    @property
    def model(self):
        return Disks._get_device_property(self._device_props, "DriveModel")

    @property
    def serial(self):
        return Disks._get_device_property(self._device_props, "DriveSerial")

    @property
    def disk_name(self):
        return '%s_%s_%s'%(self.vendor,self.model,self.serial)

    @property
    def match_pattern(self):
        return 'vendor:%s,model:%s,serial:%s'%(self.vendor,self.model,self.serial)

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

    def __str__(self):
        ret = 'vendor=' + str(self.vendor) + ' model=' + str(self.model) +\
            ' serial=' + str(self.serial) +\
            ' mounted=' + ','.join(self.mountpath) +\
            ''
        return ret

class Partition(Device):
    def __init__(self, mgr, path, device_obj, device_props):
        super(Partition, self).__init__(mgr, path, device_obj, device_props)

    @property
    def size(self):
        return Disks._get_device_property(self._device_props, "PartitionSize")

    @property
    def uuid(self):
        return Disks._get_device_property(self._device_props, "PartitionUuid")

    @property
    def label(self):
        return Disks._get_device_property(self._device_props, "PartitionLabel")

    @property
    def slave(self):
        path = Disks._get_device_property(self._device_props, "PartitionSlave")
        if path:
            ret = self._mgr._get_device_by_udisks_path(path)
        else:
            ret = None
        return ret

    def __str__(self):
        ret = 'nativepath=' + str(self.nativepath) +\
            ' uuid=' + str(self.uuid) +\
            ' label=' + str(self.label) +\
            ''
        return ret

class Lvm2PV(Partition):
    def __init__(self, mgr, path, device_obj, device_props):
        super(Lvm2PV, self).__init__(mgr, path, device_obj, device_props)

    @property
    def group_uuid(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupUuid")

    @property
    def group_name(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupName")

    @property
    def group_unallocated_size(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupUnallocatedSize")

    @property
    def group_size(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupSize")

    @property
    def group_extent_size(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupExtentSize")

    @property
    def group_num_metadata_areas(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupNumMetadataAreas")

    @property
    def group_logical_volumes(self):
        path_array = Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupLogicalVolumes")
        ret = path_array
        #ret = []
        #for path in path_array:
            #ret.append(self._mgr._get_device_by_udisks_path(path))
        return ret

    @property
    def group_physical_volumes(self):
        path_array = Disks._get_device_property(self._device_props, "LinuxLvm2PVGroupPhysicalVolumes")
        ret = path_array
        #ret = []
        #for path in path_array:
            #ret.append(self._mgr._get_device_by_udisks_path(path))
        return ret

    @property
    def uuid(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2PVUuid")

    def __str__(self):
        ret = 'nativepath=' + str(self.nativepath) +\
            ' uuid=' + str(self.uuid) +\
            ' groupUuid=' + str(self.group_uuid) +\
            ' groupName=' + str(self.group_name) +\
            ' logical_volumes=' + str(self.group_logical_volumes) +\
            ' physical_volumes=' + str(self.group_physical_volumes) +\
            ''
        return ret

class Lvm2LV(Device):
    def __init__(self, mgr, path, device_obj, device_props):
        super(Lvm2LV, self).__init__(mgr, path, device_obj, device_props)

    @property
    def group_uuid(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2LVGroupUuid")

    @property
    def group_name(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2LVGroupName")

    @property
    def group_devices(self):
        return self._mgr._get_devices_by_lvm2_lvgroup_uuid(self.group_uuid)

    @property
    def uuid(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2LVUuid")

    @property
    def name(self):
        return Disks._get_device_property(self._device_props, "LinuxLvm2LVName")

    def __str__(self):
        ret = 'nativepath=' + str(self.nativepath) +\
            ' uuid=' + str(self.uuid) +\
            ' name=' + str(self.name) +\
            ' groupUuid=' + str(self.group_uuid) +\
            ' groupName=' + str(self.group_name) +\
            ' groupDevices=' + str(self.group_devices) +\
            ''
        return ret

class Disks(object):
    _dbus_system_bus = None
    _udisks_manager_obj = None
    _udisks_manager = None

    DEVICE_CLASS = 'org.freedesktop.UDisks.Device'

    def __init__(self):
        self._rescan()
        
    @staticmethod
    def _dbus_get_device(path):
        device_obj = Disks._dbus_system_bus.get_object("org.freedesktop.UDisks", path)
        if device_obj is not None:
            device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
        else:
            device_props = None
        return (device_obj, device_props)

    @staticmethod
    def _get_device_property(device_props, property_name):
        return device_props.Get(Disks.DEVICE_CLASS, property_name)

    @staticmethod
    def _dbus_connect():
        if Disks._dbus_system_bus is None:
            Disks._dbus_system_bus = dbus.SystemBus()
            Disks._udisks_manager_obj = Disks._dbus_system_bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
            Disks._udisks_manager = dbus.Interface(Disks._udisks_manager_obj, 'org.freedesktop.UDisks')
        return True if Disks._udisks_manager is not None else False

    @staticmethod
    def _create_device(mgr, path):
        (device_obj, device_props) = Disks._dbus_get_device(path)
        if device_obj and device_props:
            is_drive = Disks._get_device_property(device_props, "DeviceIsDrive")
            is_partition = Disks._get_device_property(device_props, "DeviceIsPartition")
            is_lvm2lv = Disks._get_device_property(device_props, "DeviceIsLinuxLvm2LV")
            is_lvm2pv = Disks._get_device_property(device_props, "DeviceIsLinuxLvm2PV")
            if is_drive:
                print('create disk %s' % (path))
                ret = Disk(mgr, path, device_obj, device_props)
            elif is_lvm2pv:
                print('create Lvm2PV %s' % (path))
                ret = Lvm2PV(mgr, path, device_obj, device_props)
            elif is_partition:
                print('create partition %s' % (path))
                ret = Partition(mgr, path, device_obj, device_props)
            elif is_lvm2lv:
                print('create Lvm2LV %s' % (path))
                ret = Lvm2LV(mgr, path, device_obj, device_props)
            else:
                print('create device %s' % (path))
                ret = Device(mgr, path, device_obj, device_props)
        else:
            ret = None
        return ret

    def _rescan(self):
        self._list = []
        if not Disks._dbus_connect():
            return False
        for path in Disks._udisks_manager.EnumerateDevices():
            self._list.append(Disks._create_device(self, path))
        ret = True
        return ret
    
    def _get_device_by_udisks_path(self, path):
        ret = None
        for dev in self._list:
            if dev.path == path:
                ret = dev
        if ret is None:
            ret = Disks._create_device(self, path)
        return ret

    def _get_devices_by_lvm2_lvgroup_uuid(self, group_uuid):
        ret = []
        for dev in self._list:
            if isinstance(dev, Lvm2PV) and dev.group_uuid == group_uuid:
                ret.append(dev)
        return ret

    def find_disk(self, devfile):
        if not Disks._dbus_connect():
            return None
        path = Disks._udisks_manager.FindDeviceByDeviceFile(devfile)
        if path:
            ret = self._get_device_by_udisks_path(path)
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
    
    def _get_list(self, include_removal=False):
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
    def devices(self):
        return self._list

    @property
    def disks(self):
        return self._get_list(include_removal=True)

    @property
    def fixed_disks(self):
        return self._get_list(include_removal=False)

    @property
    def root_partition(self):
        ret = None
        for d in self._list:
            if ( isinstance(d, Partition) or isinstance(d, Lvm2LV) ) and d.is_mounted and '/' in d.mountpath:
                ret = d
        return ret

    @property
    def system_disk(self):
        part = self.root_partition
        if part is not None:
            if isinstance(part, Partition):
                ret = part.slave
            elif isinstance(part, Lvm2LV):
                ret = []
                print('got group devices=' + str(part.group_devices))
                for dev in part.group_devices:
                    if isinstance(dev, Partition):
                        ret.append(dev.slave)
            else:
                ret = None
        else:
            ret = None
        return ret

if __name__ == '__main__':
    
    e = Disks()
    print('devices:')
    for dev in e.devices:
        print(dev)
    print('disks:')
    for disk in e.disks:
        print(disk)

    print('root partition:')
    print(e.root_partition)

    print('system drive:')
    print(e.system_disk)
