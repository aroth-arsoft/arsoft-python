#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.disks.edskmgr import ExternalDiskManager

class DiskManager(object):
    def __init__(self, tag=None, root_dir=None):
        self._tag = tag
        self._mgr = ExternalDiskManager(trigger='arsoft-backup')
        self._mgr.load_config(root_dir=root_dir)
    
    @property 
    def disk_tag(self):
        return self._tag

    def cleanup(self):
        self._mgr.cleanup()

    def eject(self, disk_obj):
        return self._mgr.remove_disk(disk_obj)

    def load(self):
        return self._mgr.rescan_empty_scsi_hosts()
    
    def is_disk_ready(self):
        ret = True
        if self._tag is not None:
            # do not wait for a disk, just check if we got one
            if not self._mgr.wait_for_disk(tag=self._tag, timeout=None):
                ret = False
        return ret
    
    def wait_for_disk(self, timeout=30.0):
        if self._tag is None:
            return None
        disk = self._mgr.wait_for_disk(tag=self._tag, timeout=timeout)
        return disk

    def get_disk(self):
        if self._tag is None:
            return None
        disk = self._mgr.wait_for_disk(tag=self._tag, timeout=None)
        return disk

    def get_disk_for_directory(self, dir):
        return self._mgr.get_disk_for_file(dir)

    def get_disk_mountpath(self, disk_obj):
        ret = None
        for fs_obj in disk_obj.filesystems:
            mountpoints = fs_obj.mountpoints
            if mountpoints is not None and mountpoints:
                ret = mountpoints[0]
                break
        return ret

    def disk_mount(self, disk_obj):
        ret = (False, None)
        for fs_obj in disk_obj.filesystems:
            mountpoints = fs_obj.mountpoints
            if mountpoints is not None and len(mountpoints) == 0:
                ret = fs_obj.mount()
                break
        return ret

 
if __name__ == "__main__":
    dm = DiskManager()
