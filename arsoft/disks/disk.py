#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import dbus
import os.path
import stat
import re

class Device(object):
    DEVICE_CLASS = 'org.freedesktop.UDisks.Device'
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        self._mgr = mgr
        self._path = path
        self._device_obj = device_obj
        self._device_props = device_props
        self._device_if = device_if

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
    def mountpaths(self):
        tmp = Disks._get_device_property(self._device_props, "DeviceMountPaths")
        if isinstance(tmp, dbus.Array):
            ret = []
            for a in tmp:
                ret.append(str(a))
        else:
            ret = None
        return ret

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
        ret = '' +\
            'path=' + str(self.path) +\
            ' nativepath=' + str(self.nativepath) +\
            ''
        return ret

class Disk(Device):
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        super(Disk, self).__init__(mgr, path, device_obj, device_props, device_if)

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
        s = '%s_%s_%s'%(self.vendor,self.model,self.serial)
        return re.sub('[^\w\-_\. ]', '_', s)

    @property
    def match_pattern(self):
        return 'vendor:%s,model:%s,serial:%s'%(self.vendor,self.model,self.serial)

    @property
    def childs(self):
        return self._mgr.get_partitions(self)

    @property
    def partitions(self):
        return self._mgr.get_partitions(self)

    @property
    def is_system_disk(self):
        root_part = self._mgr.root_partition
        parts = self._mgr.get_partitions(self)
        ret = True if root_part in parts else False
        return ret

    def eject(self, options=[]):
        self._device_if.DriveEject(options)

    def detach(self, options=[]):
        self._device_if.DriveDetach(options)
        
    def _match_pattern_element(self, pattern_element):
        # check for valid pattern
        if ':' in pattern_element:
            key, value = pattern_element.split(':')
        else:
            # no valid pattern, so treat it like a serial number
            key = 'serial'
            value = pattern_element
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

    def match(self, pattern):
        elements = pattern.split(',')
        if len(elements) == 0:
            ret = False
        else:
            ret = True
            for e in elements:
                if not self._match_pattern_element(e):
                    ret = False
                    break
        #print('match this=' + str(self) + ' pa=' + pattern + ' ret='+str(ret))
        return ret

    def __str__(self):
        ret = Device.__str__(self) +\
            ' vendor=' + str(self.vendor) + \
            ' model=' + str(self.model) +\
            ' serial=' + str(self.serial) +\
            ' mounted=' + ','.join(self.mountpaths) +\
            ''
        return ret

class Floppy(Device):
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        super(Floppy, self).__init__(mgr, path, device_obj, device_props, device_if)

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
        s = '%s_%s_%s'%(self.vendor,self.model,self.serial)
        return re.sub('[^\w\-_\. ]', '_', s)

    @property
    def match_pattern(self):
        return 'vendor:%s,model:%s,serial:%s'%(self.vendor,self.model,self.serial)

    def _match_pattern_element(self, pattern_element):
        # check for valid pattern
        if ':' in pattern_element:
            key, value = pattern_element.split(':')
        else:
            # no valid pattern, so treat it like a serial number
            key = 'serial'
            value = pattern_element
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

    def match(self, pattern):
        elements = pattern.split(',')
        if len(elements) == 0:
            ret = False
        else:
            ret = True
            for e in elements:
                if not self._match_pattern_element(e):
                    ret = False
                    break
        #print('match this=' + str(self) + ' pa=' + pattern + ' ret='+str(ret))
        return ret

    def __str__(self):
        ret = Device.__str__(self) +\
            ' vendor=' + str(self.vendor) + \
            ' model=' + str(self.model) +\
            ' serial=' + str(self.serial) +\
            ' mounted=' + ','.join(self.mountpaths) +\
            ''
        return ret

class Partition(Device):
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        super(Partition, self).__init__(mgr, path, device_obj, device_props, device_if)

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

    def mount(self, filesystem_type='', options=[]):
        try:
            self._device_if.FilesystemMount(filesystem_type, options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return ret

    def unmount(self, options=[]):
        try:
            self._device_if.FilesystemUnmount(options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return ret

    def set_label(self, new_label):
        try:
            self._device_if.FilesystemSetLabel(new_label)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return ret

    def __str__(self):
        ret = Device.__str__(self) +\
            ' uuid=' + str(self.uuid) +\
            ' label=' + str(self.label) +\
            ''
        return ret

class Lvm2PV(Partition):
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        super(Lvm2PV, self).__init__(mgr, path, device_obj, device_props, device_if)

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
        ret = Partition.__str__(self) +\
            ' uuid=' + str(self.uuid) +\
            ' groupUuid=' + str(self.group_uuid) +\
            ' groupName=' + str(self.group_name) +\
            ' logical_volumes=' + str(self.group_logical_volumes) +\
            ' physical_volumes=' + str(self.group_physical_volumes) +\
            ''
        return ret

class Lvm2LV(Device):
    def __init__(self, mgr, path, device_obj, device_props, device_if):
        super(Lvm2LV, self).__init__(mgr, path, device_obj, device_props, device_if)

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

    def stop(self, options=[]):
        self._device_if.LinuxLvm2LVStop(options)

    def __str__(self):
        ret = Device.__str__(self) +\
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
        self._last_error = None
        self.rescan()
        
    @staticmethod
    def _dbus_get_device(path):
        device_obj = Disks._dbus_system_bus.get_object("org.freedesktop.UDisks", path)
        if device_obj is not None:
            device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
            device_if = dbus.Interface(device_obj, Disks.DEVICE_CLASS)
        else:
            device_props = None
            device_if = None
        return (device_obj, device_props, device_if)

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
        (device_obj, device_props, device_if) = Disks._dbus_get_device(path)
        if device_obj and device_props:
            is_drive = Disks._get_device_property(device_props, "DeviceIsDrive")
            is_partition = Disks._get_device_property(device_props, "DeviceIsPartition")
            is_lvm2lv = Disks._get_device_property(device_props, "DeviceIsLinuxLvm2LV")
            is_lvm2pv = Disks._get_device_property(device_props, "DeviceIsLinuxLvm2PV")
            if is_drive:
                media_compatibility = Disks._get_device_property(device_props, "DriveMediaCompatibility")
                #print('media_compatibility=%s' % media_compatibility)
                if 'floppy' in media_compatibility:
                    ret = Floppy(mgr, path, device_obj, device_props, device_if)
                else:
                    #print('create disk %s' % (path))
                    ret = Disk(mgr, path, device_obj, device_props, device_if)
            elif is_lvm2pv:
                #print('create Lvm2PV %s' % (path))
                ret = Lvm2PV(mgr, path, device_obj, device_props, device_if)
            elif is_partition:
                #print('create partition %s' % (path))
                ret = Partition(mgr, path, device_obj, device_props, device_if)
            elif is_lvm2lv:
                #print('create Lvm2LV %s' % (path))
                ret = Lvm2LV(mgr, path, device_obj, device_props, device_if)
            else:
                #print('create device %s' % (path))
                ret = Device(mgr, path, device_obj, device_props, device_if)
        else:
            ret = None
        return ret
    
    @property
    def last_error(self):
        return self._last_error

    def rescan(self):
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
    
    def _get_device_by_devpath(self, devpath):
        ret = None
        if devpath[0] != '/':
            devpath = os.path.join('/sys', devpath)
        elif devpath.startswith('/devices/'):
            devpath = '/sys' + devpath
        for dev in self._list:
            #print('compare %s<>%s' % (dev.nativepath, devpath))
            if dev.nativepath == devpath:
                ret = dev
        return ret

    def _get_devices_by_lvm2_lvgroup_uuid(self, group_uuid):
        ret = []
        for dev in self._list:
            if isinstance(dev, Lvm2PV) and dev.group_uuid == group_uuid:
                ret.append(dev)
        return ret

    def find_device(self, devfile=None, devpath=None, dev_inode=None):
        if not Disks._dbus_connect():
            return None
        ret = None
        if dev_inode is not None:
            dev_major, dev_minor = os.major(dev_inode), os.minor(dev_inode)
            try:
                path = Disks._udisks_manager.FindDeviceByMajorMinor(dev_major, dev_minor)
                if path:
                    ret = self._get_device_by_udisks_path(path)
            except dbus.exceptions.DBusException as e:
                self._last_error = str(e)
        elif devfile is not None:
            try:
                path = Disks._udisks_manager.FindDeviceByDeviceFile(devfile)
                if path:
                    ret = self._get_device_by_udisks_path(path)
            except dbus.exceptions.DBusException as e:
                self._last_error = str(e)
        elif devpath is not None:
            ret = self._get_device_by_devpath(devpath)
        return ret

    def find_device_for_file(self, path):
        ret = None
        if os.path.exists(path):
            # given argument might be a device file
            s = os.stat(path)
            if stat.S_ISBLK(s.st_mode):
                ret = self.find_device(devfile=path)
            elif stat.S_ISDIR(s.st_mode) or stat.S_ISFILE(s.st_mode):
                ret = self.find_device(dev_inode=s.st_dev)
        return ret

    def find_disk_for_file(self, path):
        ret = self.find_device_for_file(path)
        if ret:
            if not isinstance(ret, Disk):
                ret = self.find_disk_for_device(ret)
        return ret

    def find_disk_from_devpath(self, devpath):
        ret = self.find_device(devpath=devpath)
        if ret:
            if not isinstance(ret, Disk):
                ret = self.find_disk_for_device(ret)
        return ret

    def find_disk_from_user_input(self, devname):
        if os.path.exists(devname):
            # given argument might be a device file
            s = os.stat(devname)
            if stat.S_ISBLK(s.st_mode):
                ret = self.find_device(devfile=devname)
            elif stat.S_ISDIR(s.st_mode):
                ret = self.find_device(devpath=devname)
            else:
                ret = None
        elif devname.startswith('/sys/') or devname.startswith('/devices/'):
            ret = self.find_device(devpath=devname)
        else:
            ret = None
        if ret:
            if not isinstance(ret, Disk):
                ret = self.find_disk_for_device(ret)
        return ret
    
    def find_disk_for_device(self, devobj):
        if isinstance(devobj, Partition):
            ret = devobj.slave
        elif isinstance(devobj, Lvm2LV):
            ret = []
            #print('got group devices=' + str(devobj.group_devices))
            for dev in devobj.group_devices:
                if isinstance(dev, Partition):
                    ret.append(dev.slave)
            if len(ret) == 1:
                ret = ret[0]
        else:
            ret = None
        return ret
    
    def find_disk_by_pattern(self, pattern):
        ret = None
        for devobj in self._list:
            if isinstance(devobj, Disk):
                if isinstance(pattern, list):
                    for p in pattern:
                        if devobj.match(p):
                            ret = devobj
                            break
                    if ret:
                        break
                else:
                    if devobj.match(pattern):
                        ret = devobj
                        break
        return ret

    def __str__(self):
        ret = ''
        for d in self._list:
            ret = ret + str(d) + "\n"
        return ret

    def get_partitions(self, disk_obj=None):
        ret = []
        for devobj in self._list:
            if isinstance(devobj, Partition):
                if disk_obj is None:
                    ret.append(devobj)
                else:
                    slave = devobj.slave
                    if slave and slave.nativepath == disk_obj.nativepath:
                        ret.append(devobj)
            elif isinstance(devobj, Lvm2LV):
                for dev in devobj.group_devices:
                    if isinstance(dev, Partition):
                        if disk_obj is None:
                            ret.append(devobj)
                        else:
                            slave = dev.slave
                            if slave and slave.nativepath == disk_obj.nativepath:
                                ret.append(devobj)
        return ret

    @property
    def devices(self):
        return self._list

    @property
    def partitions(self):
        return self.get_partitions(disk_obj=None)

    @property
    def disks(self):
        ret = []
        for d in self._list:
            if isinstance(d, Disk):
                ret.append(d)
        return ret

    @property
    def fixed_disks(self):
        ret = []
        for d in self._list:
            if isinstance(d, Disk) and d.is_removable:
                ret.append(d)
        return ret

    @property
    def root_partition(self):
        ret = None
        for d in self._list:
            if ( isinstance(d, Partition) or isinstance(d, Lvm2LV) ) and d.is_mounted and '/' in d.mountpaths:
                ret = d
        return ret

    @property
    def system_disk(self):
        part = self.root_partition
        if part is not None:
            ret = self.find_disk_for_device(part)
        else:
            ret = None
        return ret

if __name__ == '__main__':
    
    e = Disks()
    print('devices:')
    for obj in e.devices:
        print('  ' + str(obj))

    print('disks:')
    for obj in e.disks:
        print('  %s %s (%s)'%(str(obj.vendor), str(obj.model), str(obj.serial)))
        for child in obj.childs:
            print('    %s'%(str(child.nativepath)))

    print('partitions:')
    for obj in e.partitions:
        print('  ' + str(obj))

    print('root partition:')
    print(e.root_partition)

    print('system disk:')
    print(e.system_disk)

    root_disk = e.find_disk_for_file('/')
    print('root disk:')
    print(root_disk)
