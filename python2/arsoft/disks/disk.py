#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import dbus
import os.path
import stat
import re

class Device(object):
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        self._mgr = mgr
        self._path = path
        self._dev_obj = dev_obj
        self._obj_iface_and_props = obj_iface_and_props

    @property
    def path(self):
        return self._path

    @property
    def is_block(self):
        return True if Block.INTERFACE_NAME in self._obj_iface_and_props else False
    @property
    def is_drive(self):
        return True if Drive.INTERFACE_NAME in self._obj_iface_and_props else False
    @property
    def is_partition(self):
        return True if Partition.INTERFACE_NAME in self._obj_iface_and_props else False
    @property
    def is_loop(self):
        return True if Loop.INTERFACE_NAME in self._obj_iface_and_props else False
    @property
    def is_filesystem(self):
        return True if Filesystem.INTERFACE_NAME in self._obj_iface_and_props else False

    INTERFACE_NAME = 'org.freedesktop.UDisks2.Partition'

    @staticmethod
    def _readfile(path, strip=True):
        try:
            f = open(path, 'r')
            ret = f.read().strip()
            f.close()
        except IOError:
            ret = None
        return ret


    @staticmethod
    def _bytearray_to_string(array, encoding='utf8'):
        if isinstance(array, dbus.Array):
            ret = bytearray()
            for a in array:
                if a != 0:
                    ret.append(a)
            return ret.decode(encoding)
        else:
            return array

    def _get_obj_property(self, iface_name, prop_name, default_value=None):
        if iface_name in self._obj_iface_and_props:
            return self._obj_iface_and_props[iface_name].get(prop_name, default_value)
        else:
            return default_value

    def _get_obj_property_byte_array(self, iface_name, prop_name, default_value=None):
        if iface_name in self._obj_iface_and_props:
            return Device._bytearray_to_string(self._obj_iface_and_props[iface_name].get(prop_name, default_value))
        else:
            return default_value

    def _get_obj_property_array_of_byte_array(self, iface_name, prop_name, default_value=None):
        if iface_name in self._obj_iface_and_props:
            tmp = self._obj_iface_and_props[iface_name].get(prop_name, default_value)
            if isinstance(tmp, dbus.Array):
                ret = []
                for a in tmp:
                    ret.append(Device._bytearray_to_string(a))
            else:
                ret = default_value
            return ret
        else:
            return default_value

    def __repr__(self):
        return str(type(self)) + '[' + self._path + ']'

    def __str__(self):
        ret = '' +\
            'path=' + str(self.path) +\
            ''
        return ret

class Block(Device):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Block'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(Block, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._block_iface = dbus.Interface(dev_obj, Block.INTERFACE_NAME)

        drive = self.table if self.is_partition else None
        if drive:
            self._sysfs_path = os.path.join('/sys/block', os.path.basename(drive), os.path.basename(self.device))
        else:
            self._sysfs_path = os.path.join('/sys/block', os.path.basename(self.device))
        if not os.path.exists(self._sysfs_path):
            self._sysfs_path = None

    @property
    def sysfs_path(self):
        return self._sysfs_path

    @property
    def slaves(self):
        if not self._sysfs_path:
            return None
        ret = []
        slaves_dir = os.path.join(self._sysfs_path, 'slaves')
        if os.path.isdir(slaves_dir):
            for f in os.listdir(slaves_dir):
                slave_dev = os.path.join(slaves_dir, f, 'dev')
                devno_str = Device._readfile(slave_dev)
                if devno_str:
                    dev_major_str, dev_minor_str = devno_str.split(':')
                    dev_major = int(dev_major_str)
                    dev_minor = int(dev_minor_str)
                    devobj = self._mgr.find_device(dev_inode=os.makedev(dev_major, dev_minor))
                    if devobj:
                        ret.append(devobj)
        return ret

    @property
    def device(self):
        return self._get_obj_property_byte_array(Block.INTERFACE_NAME, 'Device')

    @property
    def preferred_device(self):
        return self._get_obj_property_byte_array(Block.INTERFACE_NAME, "PreferredDevice")

    @property
    def symlinks(self):
        return self._get_obj_property_array_of_byte_array(Block.INTERFACE_NAME, 'Symlinks')

    @property
    def drive(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "Drive")

    @property
    def id(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "Id")

    @property
    def id_usage(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "IdUsage")

    @property
    def id_uuid(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "IdUUID")

    @property
    def id_label(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "IdLabel")

    @property
    def id_type(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "IdType")

    @property
    def id_version(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "IdVersion")

    @property
    def device_number(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "DeviceNumber")

    @property
    def size(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "Size")

    @property
    def hint_auto(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "HintAuto")

    @property
    def hint_system(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "HintSystem")

    @property
    def hint_name(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "HintName")

    @property
    def hint_icon_name(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "HintIconName")

    @property
    def hint_symbolic_icon_name(self):
        return self._get_obj_property(Block.INTERFACE_NAME, "HintSymbolicIconName")

    def __repr__(self):
        return str(type(self)) + '[%s, %s]' % (self.path, self.device)

    def __str__(self):
        ret = '' +\
            'path=' + str(self.path) +\
            ' device=' + str(self.device) +\
            ''
        return ret

class Loop(Block):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Loop'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(Loop, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._loop_iface = dbus.Interface(dev_obj, Loop.INTERFACE_NAME)

class Drive(Device):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Drive'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(Drive, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._drive_iface = dbus.Interface(dev_obj, Drive.INTERFACE_NAME)

    @property
    def vendor(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Vendor")

    @property
    def model(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Model")

    @property
    def serial(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Serial")

    @property
    def revision(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Revision")

    @property
    def is_removable(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Removable")

    @property
    def is_optical(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Optical")

    @property
    def is_optical_blank(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "OpticalBlank")

    @property
    def is_ejectable(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "Ejectable")

    @property
    def is_media_available(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "MediaAvailable")

    @property
    def is_media_removable(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "MediaRemovable")

    @property
    def has_media_change_detected(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "MediaChangeDetected")

    @property
    def can_poweroff(self):
        return self._get_obj_property(Drive.INTERFACE_NAME, "CanPowerOff")

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
        root_fs = self._mgr.root_filesystem
        parts = self._mgr.get_partitions(self)
        ret = True if root_fs in parts else False
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
            ''
        return ret

class Partition(Block):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Partition'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(Partition, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._partition_iface = dbus.Interface(dev_obj, Partition.INTERFACE_NAME)

    @property
    def offset(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Offset")

    @property
    def size(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Size")

    @property
    def flags(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Flags")

    @property
    def uuid(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, 'UUID')

    @property
    def name(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, 'Name')

    @property
    def number(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Number")

    @property
    def type(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Type")

    @property
    def table(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "Table")

    @property
    def is_container(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "IsContainer")

    @property
    def is_contained(self):
        return self._get_obj_property(Partition.INTERFACE_NAME, "IsContained")

    @property
    def parent_device(self):
        parent_path = self.table
        return self._mgr.find_device(parent_path)

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
            ' name=' + str(self.name) +\
            ''
        return ret

class FilesystemWithPartition(Partition):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Filesystem'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(FilesystemWithPartition, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._filesystem_iface = dbus.Interface(dev_obj, FilesystemWithPartition.INTERFACE_NAME)

    def mount(self, filesystem_type='', options=[]):
        mountpath = None
        try:
            mountpath = self._filesystem_iface.Mount(filesystem_type, options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return (ret, mountpath)

    def unmount(self, options=[]):
        try:
            self._filesystem_iface.Unmount(options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return ret

    @property
    def is_mounted(self):
        pt = self.mountpoints
        if pt is None:
            return False
        else:
            return True if pt else False

    @property
    def mountpoints(self):
        return self._get_obj_property_array_of_byte_array(FilesystemWithPartition.INTERFACE_NAME, 'MountPoints')

class Filesystem(Block):
    INTERFACE_NAME = 'org.freedesktop.UDisks2.Filesystem'
    def __init__(self, mgr, path, dev_obj, obj_iface_and_props):
        super(Filesystem, self).__init__(mgr, path, dev_obj, obj_iface_and_props)
        self._filesystem_iface = dbus.Interface(dev_obj, Filesystem.INTERFACE_NAME)

    def mount(self, filesystem_type='', options=[]):
        mountpath = None
        try:
            mountpath = self._filesystem_iface.Mount(filesystem_type, options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return (ret, mountpath)

    def unmount(self, options=[]):
        try:
            self._filesystem_iface.Unmount(options)
            ret = True
        except dbus.exceptions.DBusException as e:
            self._mgr._last_error = str(e)
            ret = False
        return ret

    @property
    def is_mounted(self):
        pt = self.mountpoints
        if pt is None:
            return False
        else:
            return True if pt else False

    @property
    def mountpoints(self):
        return self._get_obj_property_array_of_byte_array(Filesystem.INTERFACE_NAME, 'MountPoints')

class Disks(object):
    _dbus_system_bus = None
    _udisks_manager_obj = None
    _udisks_manager = None
    _udisks_manager_drives = None
    _udisks_manager_drives_obj = None

    SERVICE_NAME = "org.freedesktop.UDisks2"
    DEVICE_CLASS = 'org.freedesktop.UDisks2.Device'

    def __init__(self):
        self._last_error = None
        self.rescan()

    @staticmethod
    def _dbus_connect():
        if Disks._dbus_system_bus is None:
            Disks._dbus_system_bus = dbus.SystemBus()
            Disks._udisks_manager_obj = Disks._dbus_system_bus.get_object(Disks.SERVICE_NAME, "/org/freedesktop/UDisks2")
            Disks._udisks_manager = dbus.Interface(Disks._udisks_manager_obj, 'org.freedesktop.DBus.ObjectManager')
        return True if Disks._udisks_manager is not None else False

    @staticmethod
    def _create_device(mgr, path, obj_iface_and_props):
        if obj_iface_and_props:
            dev_obj = Disks._dbus_system_bus.get_object(Disks.SERVICE_NAME, path)

            is_block = True if Block.INTERFACE_NAME in obj_iface_and_props else False
            is_drive = True if Drive.INTERFACE_NAME in obj_iface_and_props else False
            is_partition = True if Partition.INTERFACE_NAME in obj_iface_and_props else False
            is_loop = True if Loop.INTERFACE_NAME in obj_iface_and_props else False
            is_filesystem = True if Filesystem.INTERFACE_NAME in obj_iface_and_props else False
            if is_drive:
                ret = Drive(mgr, path, dev_obj, obj_iface_and_props)
            #elif is_lvm2pv:
                ##print('create Lvm2PV %s' % (path))
                #ret = Lvm2PV(mgr, path, obj_iface_and_props)
            elif is_loop:
                #print('create partition %s' % (path))
                ret = Loop(mgr, path, dev_obj, obj_iface_and_props)
            elif is_filesystem:
                if is_partition:
                    ret = FilesystemWithPartition(mgr, path, dev_obj, obj_iface_and_props)
                else:
                #print('create partition %s' % (path))
                    ret = Filesystem(mgr, path, dev_obj, obj_iface_and_props)
            elif is_partition:
                #print('create partition %s' % (path))
                ret = Partition(mgr, path, dev_obj, obj_iface_and_props)
            elif is_block:
                #print('create partition %s' % (path))
                ret = Block(mgr, path, dev_obj, obj_iface_and_props)
            #elif is_lvm2lv:
                ##print('create Lvm2LV %s' % (path))
                #ret = Lvm2LV(mgr, path, obj_iface_and_props)
            else:
                ret = Device(mgr, path, dev_obj, obj_iface_and_props)
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
        for obj_path, obj_iface_and_props in Disks._udisks_manager.GetManagedObjects().items():
            self._list.append(Disks._create_device(self, obj_path, obj_iface_and_props))
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
            if dev.path == devpath:
                ret = dev
        return ret

    def find_device(self, devfile=None, devpath=None, dev_inode=None):
        if not Disks._dbus_connect():
            return None
        ret = None
        if dev_inode is not None:
            for d in self._list:
                if isinstance(d, Block):
                    if d.device_number == dev_inode:
                        ret = d
                        break
        elif devfile is not None:
            for d in self._list:
                if isinstance(d, Block):
                    if d.device == devfile or d.preferred_device == devfile or devfile in d.symlinks:
                        ret = d
                        break
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

    def find_drive_for_file(self, path):
        ret = self.find_device_for_file(path)
        if ret:
            if not isinstance(ret, Drive):
                ret = self.find_drive_for_device(ret)
        return ret

    def find_drive_from_devpath(self, devpath):
        ret = self.find_device(devpath=devpath)
        if ret:
            if not isinstance(ret, Drive):
                ret = self.find_drive_for_device(ret)
        return ret

    def find_device_from_udisks_path(self, path):
        return self._get_device_by_devpath(path)

    def find_drive_from_user_input(self, devname):
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
        elif devname.startswith('/org/freedesktop/UDisks2'):
            ret = self._get_device_by_devpath(devname)
        else:
            ret = self.find_drive_by_pattern(devname)
        if ret:
            if not isinstance(ret, Drive):
                ret = self.find_drive_for_device(ret)
        return ret
    
    def find_drive_for_device(self, devobj):
        if devobj.is_drive:
            ret = devobj
        elif devobj.is_partition:
            ret = self.find_drive_from_devpath(devobj.table)
        elif devobj.is_block:
            ret = None
            if devobj.drive != '/':
                ret = self.find_drive_from_devpath(devobj.drive)
            if not ret:
                for slave in devobj.slaves:
                    slave_drive = self.find_drive_for_device(slave)
                    if slave_drive:
                        ret = slave_drive
                        break
        else:
            ret = None
        return ret
    
    def find_drive_by_pattern(self, pattern):
        ret = None
        for devobj in self._list:
            if isinstance(devobj, Drive):
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
                    parent_path = devobj.table
                    if parent_path == disk_obj.path:
                        ret.append(devobj)
        return ret

    @property
    def devices(self):
        return self._list

    @property
    def partitions(self):
        return self.get_partitions(disk_obj=None)

    @property
    def blocks(self):
        ret = []
        for d in self._list:
            if isinstance(d, Block):
                ret.append(d)
        return ret

    @property
    def drives(self):
        ret = []
        for d in self._list:
            if isinstance(d, Drive):
                ret.append(d)
        return ret

    @property
    def loops(self):
        ret = []
        for d in self._list:
            if isinstance(d, Loop):
                ret.append(d)
        return ret

    @property
    def filesystems(self):
        ret = []
        for d in self._list:
            if isinstance(d, Filesystem) or isinstance(d, FilesystemWithPartition):
                ret.append(d)
        return ret

    @property
    def fixed_drives(self):
        ret = []
        for d in self._list:
            if isinstance(d, Drive) and d.is_removable:
                ret.append(d)
        return ret

    @property
    def root_filesystem(self):
        ret = None
        for d in self.filesystems:
            if isinstance(d, Filesystem):
                if d.is_mounted and '/' in d.mountpoints:
                    ret = d
        return ret

    @property
    def system_drive(self):
        root_fs = self.root_filesystem
        if root_fs is not None:
            ret = self.find_drive_for_device(root_fs)
        else:
            ret = None
        return ret

if __name__ == '__main__':
    
    e = Disks()
    print('devices:')
    for obj in e.devices:
        print('  ' + str(obj))

    print('drives:')
    for obj in e.drives:
        print('  %s %s (%s)'%(str(obj.vendor), str(obj.model), str(obj.serial)))
        for child in obj.childs:
            print('    %s'%(str(child.nativepath)))

    print('partitions:')
    for obj in e.partitions:
        print('  ' + str(obj))

    print('loops:')
    for obj in e.loops:
        print('  ' + str(obj))

    print('filesystems:')
    for obj in e.filesystems:
        print('  ' + str(obj))

    print('root filesystem:')
    print(e.root_filesystem)

    print('system drive:')
    print(e.system_drive)

    root_drive = e.find_drive_for_file('/')
    print('root drive:')
    print(root_drive)
