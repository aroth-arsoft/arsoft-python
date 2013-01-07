#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import re

class Scsi(object):
    
    HOSTADDRLINE_RE = re.compile(
        r'^Host:\s+(?P<host>[a-zA-Z0-9]+)\s+Channel:\s+(?P<channel>[0-9]+)\s+Id:\s+(?P<id>[0-9]+)\s+Lun:\s+(?P<lun>[0-9]+)'
        )
    VERNDORMODELLINE_RE = re.compile(
        r'\s+Vendor:\s+(?P<vendor>[a-zA-Z\-_0-9]+)\s+Model:\s+(?P<model>[a-zA-Z \-_0-9]+)\s+Rev:\s+(?P<rev>[a-zA-Z\-_0-9]+)'
        )
    TYPELINE_RE = re.compile(
        r'\s+Type:\s+(?P<type>[a-zA-Z\-_0-9]+)\s+(ANSI)\s+SCSI revision:\s+(?P<scsi_rev>[0-9]+)'
        )
    
    def __init__(self, path=None):
        self._devices = None
        self._last_error = None
        pass
    
    
    def _retrieve_devices(self):
        self._devices = []
        try:
            ret = False
            got_header_line = False
            f = open('/proc/scsi/scsi', 'r')
            lines = f.readlines()
            if lines[0].startswith('Attached devices:'):
                index = 1
                num_lines = len(lines)
                print('num_lines=' + str(num_lines))
                while index + 2 <= num_lines:
                    mo_hostaddr = Scsi.HOSTADDRLINE_RE.match(lines[index])
                    mo_vendor = Scsi.VERNDORMODELLINE_RE.match(lines[index+1])
                    mo_type = Scsi.TYPELINE_RE.match(lines[index+2])
                    print('mo_hostaddr=' + str(mo_hostaddr))
                    print('mo_vendor=' + str(mo_vendor))
                    print('mo_type=' + str(mo_type))
                    
                    if mo_hostaddr and mo_vendor and mo_type:
                        host = mo_hostaddr.group('host')
                        channel = mo_hostaddr.group('channel')
                        id = mo_hostaddr.group('id')
                        lun = mo_hostaddr.group('lun')
                        model = mo_vendor.group('model')
                        vendor = mo_vendor.group('vendor')
                        rev = mo_vendor.group('rev')
                        devtype = mo_type.group('type')
                        scsi_rev = mo_type.group('scsi_rev')
                        
                        device = {'host':host, 'channel':channel, 'id':id, 'lun':lun, 'vendor':vendor, 'model':model, 'rev':rev, 'type':devtype, 'scsi_rev':scsi_rev }
                        self._devices.append( device )
                    index = index + 3
                    
                ret = True
            f.close()
        except IOError as e:
            self._last_error = str(e)
            ret = False
        return ret

    def rescanHost(self, host):
        try:
            f = open('/proc/scsi/scsi', 'w')
            f.write("scsi add-single-device " + host + "\n")
            f.close()
            ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False

    def ejectDevice(self, host):
        try:
            f = open('/proc/scsi/scsi', 'w')
            f.write("scsi remove-single-device " + host + "\n")
            f.close()
            ret = True
        except IOError as e:
            self._last_error = str(e)
            ret = False

    @property
    def devices(self):
        if not self._devices:
            self._retrieve_devices()
        return self._devices

    def __str__(self):
        ret = 'devices=' + str(self.devices) +\
            ''
        return ret

if __name__ == '__main__':
    
    e = Scsi()
    print('devices:')
    for device in e.devices:
        print(device)
