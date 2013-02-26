#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re
import os
import stat

class ScsiDevice(object):
    def __init__(self, host=0, channel=0, target=0, lun=0,
                    vendor=None, model=None, rev=None, scsi_level=None,
                    dev_major=0, dev_minor=0, devfile=None,
                    devtype=None, devtype_str=None):
        self.host = host
        self.channel = channel
        self.target = target
        self.lun = lun
        self.addr = (host, channel, target, lun)
        self.vendor = vendor
        self.model = model
        self.rev = rev
        self.scsi_level = scsi_level
        self.devtype = devtype
        self.devtype_str = devtype_str 
        self.dev_major = dev_major
        self.dev_minor = dev_minor
        self.devfile = devfile

    def __repr__(self):
        ret = 'addr=' + str(self.addr) +\
            ' vendor=' + str(self.vendor) +\
            ' model=' + str(self.model) +\
            ' dev=' + str(self.dev_major) + ':' + str(self.dev_minor) +\
            ' devfile=' + str(self.devfile) +\
            ''
        return ret
    def __str__(self):
        ret = 'addr=' + str(self.addr) +\
            ' vendor=' + str(self.vendor) +\
            ' model=' + str(self.model) +\
            ' dev=' + str(self.dev_major) + ':' + str(self.dev_minor) +\
            ' devfile=' + str(self.devfile) +\
            ''
        return ret

    @property
    def is_removable(self):
        return True if self.devtype in [5, 8] else False

class Scsi(object):

    SCSI_HOST_ADDR_RE = re.compile(
        r'(?P<host>[0-9]+)\:(?P<channel>[0-9]+)\:(?P<target>[0-9]+)\:(?P<lun>[0-9]+)'
        )
        
    SCSI_DEVICE_TYPES = [
        "Direct-Access", # HDD
        "Sequential-Access", # Tape
        "Printer",
        "Processor",
        "Write-once",
        "CD-ROM",
        "Scanner",
        "Optical memory",
        "Medium Changer",
        "Communications",
        "Unknown (0xa)",
        "Unknown (0xb)",
        "Storage array",
        "Enclosure",
        "Simplified direct-access",
        "Optical card read/writer",
        "Bridge controller",
        "Object based storage",
        "Automation Drive interface",
        "Reserved (0x13)", "Reserved (0x14)",
        "Reserved (0x15)", "Reserved (0x16)", "Reserved (0x17)",
        "Reserved (0x18)", "Reserved (0x19)", "Reserved (0x1a)",
        "Reserved (0x1b)", "Reserved (0x1c)", "Reserved (0x1e)",
        "Well known LU",
        "No device"
        ]
    
    def __init__(self, path=None):
        self._block_devfiles = None
        self._devices = None
        self._hosts = None
        self._last_error = None
        pass
    
    def _get_all_block_devfiles(self, devdir='/dev'):
        try:
            ret = False
            self._block_devfiles = {}
            files = os.listdir(devdir)
            for f in files:
                fullpath = os.path.join(devdir, f)
                s = os.stat(fullpath)
                if stat.S_ISBLK(s.st_mode):
                    (dev_major, dev_minor) = divmod(s.st_rdev, 256)
                    self._block_devfiles[(dev_major, dev_minor)] = fullpath
                    ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False
        return ret

    @staticmethod
    def _readfile(path, strip=True):
        try:
            f = open(path, 'r')
            ret = f.read().strip()
            f.close()
        except IOError:
            ret = None
        return ret
    
    def _dirty(self):
        self._devices = None
        self._hosts = None
    
    def _retrieve_info(self):
        self._devices = []
        self._hosts = {}
        if not self._get_all_block_devfiles():
            return False
        try:
            ret = False
            got_header_line = False
            files = os.listdir('/sys/class/scsi_host')
            for f in files:
                if f.startswith('host'):
                    hostno = int(f[4:])
                    host = {'number': hostno, 'devices': []}
                    self._hosts[hostno] = host
                    ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False
        if ret:
            try:
                ret = False
                got_header_line = False
                files = os.listdir('/sys/bus/scsi/devices')
                for f in files:
                    mo_hostaddr = Scsi.SCSI_HOST_ADDR_RE.match(f)
                    if mo_hostaddr:
                        host = int(mo_hostaddr.group('host'))
                        channel = int(mo_hostaddr.group('channel'))
                        target = int(mo_hostaddr.group('target'))
                        lun = int(mo_hostaddr.group('lun'))
                        devpath = os.path.join('/sys/bus/scsi/devices', f)
                        model = Scsi._readfile(os.path.join(devpath, 'model'))
                        vendor = Scsi._readfile(os.path.join(devpath, 'vendor'))
                        rev = Scsi._readfile(os.path.join(devpath, 'rev'))
                        scsi_level = Scsi._readfile(os.path.join(devpath, 'scsi_level'))
                        devtype = int(Scsi._readfile(os.path.join(devpath, 'type')))
                        devtype_str = Scsi.SCSI_DEVICE_TYPES[devtype]
                        
                        dev_major = 0
                        dev_minor = 0
                        devfile = None
                        devblockpath = os.path.join(devpath, 'block')
                        if os.path.exists(devblockpath):
                            files = os.listdir(devblockpath)
                            for f in files:
                                block_dev_file = os.path.join(devblockpath, f, 'dev')
                                devno_str = Scsi._readfile(block_dev_file)
                                dev_major_str, dev_minor_str = devno_str.split(':')
                                dev_major = int(dev_major_str)
                                dev_minor = int(dev_minor_str)
                                if (dev_major, dev_minor) in self._block_devfiles:
                                    devfile  = self._block_devfiles[(dev_major, dev_minor)]


                        device = ScsiDevice(host, channel, target, lun, 
                                                vendor=vendor, model=model, rev=rev,
                                                scsi_level=scsi_level, 
                                                dev_major=dev_major, dev_minor=dev_minor, devfile=devfile,
                                                devtype=devtype, devtype_str=devtype_str)
                        self._devices.append( device )
                        self._hosts[host]['devices'].append(device.addr)

                    ret = True
            except IOError as e:
                self._last_error = str(e)
                ret = False
        return ret

    def _retrieve_hosts(self):
        return ret
    
    def rescan_host(self, hostno):
        try:
            f = open('/sys/class/scsi_host/host' + str(hostno) + '/scan', 'w')
            f.write("- - -\n")
            f.close()
            self._dirty()
            ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False
        return ret
    
    def _delete_device(self, device_addr):
        (host, channel, target, lun) = device_addr
        try:
            f = open('/sys/bus/scsi/devices/%i:%i:%i:%i/delete'%(host, channel, target, lun), 'w')
            f.write("1\n")
            f.close()
            self._dirty()
            ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False
        return ret

    def delete_device_on_host(self, host):
        if host in self.hosts:
            hostinfo = self.hosts[host]
            ret = True
            for device_addr in hostinfo['devices']:
                if not self._delete_device(device_addr):
                    ret = False
        else:
            ret = False
        return ret

    def rescan_hosts(self, only_empty=False):
        ret = True
        for (hostno, hostinfo) in self.hosts.items():
            if only_empty == False:
                do_rescan = True
            else:
                do_rescan = True if len(hostinfo['devices']) == 0 else False
            if do_rescan:
                ret = self.rescan_host(hostno)
            else:
                ret = True
            if not ret:
                break
        return ret
    
    def _get_device(self, device_addr):
        ret = None
        for dev in self.devices:
            if dev.addr == device_addr:
                ret = dev
                break
        return ret

    def find_device(self, syspath):
        ret = None
        # find check for regular block devices like
        # /sys/devices/pci0000:00/0000:00:11.0/ata4/host3/target3:0:0/3:0:0:0/block/sda
        if os.path.isfile(os.path.join(syspath, 'partition')):
            scsi_device_path = os.path.join(syspath, '../device/scsi_device')
        else:
            scsi_device_path = os.path.join(syspath, 'device/scsi_device')
        if os.path.exists(scsi_device_path):
            ret = []
            files = os.listdir(scsi_device_path)
            for f in files:
                mo_hostaddr = Scsi.SCSI_HOST_ADDR_RE.match(f)
                if mo_hostaddr:
                    host = int(mo_hostaddr.group('host'))
                    channel = int(mo_hostaddr.group('channel'))
                    target = int(mo_hostaddr.group('target'))
                    lun = int(mo_hostaddr.group('lun'))
                    device_addr = (host, channel, target, lun)
                    slave_dev = self._get_device(device_addr)
                    if slave_dev is not None:
                        ret.append(slave_dev)
        else:
            dm_device_path = os.path.join(syspath, 'slaves')
            if os.path.exists(dm_device_path):
                ret = []
                files = os.listdir(dm_device_path)
                for f in files:
                    slave_sys_path = os.path.join(dm_device_path, f)
                    print('slave_sys_path=' + slave_sys_path)
                    slave_dev = self.find_device(slave_sys_path)
                    if slave_dev is not None:
                        ret.extend(slave_dev)
            else:
                # it's neither a regular block device (aka disk) nor is it a devmapper device
                pass
        return ret

    @property
    def last_error(self):
        return self._last_error

    @property
    def hosts(self):
        if not self._hosts:
            self._retrieve_info()
        return self._hosts

    @property
    def devices(self):
        if not self._devices:
            self._retrieve_info()
        return self._devices

    def __str__(self):
        ret = 'devices=' + str(self.devices) +\
            ' hosts=' + str(self.hosts) +\
            ''
        return ret

if __name__ == '__main__':
    e = Scsi()
    if e.rescan_hosts(only_empty=True):
        print('rescan_hosts successful')
    else:
        print('rescan_hosts failed')
    print('devices:')
    for device in e.devices:
        print(device)
    print('hosts:')
    for (hostno, hostinfo) in e.hosts.items():
        print(str(hostno) + ': ' + str(hostinfo))
        
    dev = e.find_device('/sys/devices/pci0000:00/0000:00:11.0/ata4/host3/target3:0:0/3:0:0:0/block/sda')
    print(dev)
    dev = e.find_device('/sys/devices/pci0000:00/0000:00:11.0/ata4/host3/target3:0:0/3:0:0:0/block/sda/sda1')
    print(dev)
    dev = e.find_device('/sys/devices/virtual/block/dm-1')
    print(dev)
