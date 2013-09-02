#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.disks.edskmgr import ExternalDiskManager

class DiskManager(object):
    def __init__(self):
        self._mgr = ExternalDiskManager()
        self._mgr.read_config()

    def cleanup(self):
        self._mgr.cleanup()

    def eject(self):
        return self._mgr.remove_external_disks()

    def load(self):
        return self._mgr.rescan_empty_scsi_hosts()
    
    def is_disk_ready(self):
        return True
 
if __name__ == "__main__":
    dm = DiskManager()
    