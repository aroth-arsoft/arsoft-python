"""This module provides a general interface to EFI variables using platform-
specific methods. Current Windows and Linux (with sysfs and efivars) are
supported.

Under Windows the pywin32 extensions are required.
"""

import os.path
import platform
import re

if platform.system() == 'Windows':
    import ctypes
    import win32api, win32process, win32security


class EfiVariables(object):
    """Abstract EFI variable access class.
    Use get_instance to create an instance for the current operating system."""
    
    def read(self, name, guid):
        raise NotImplementedError
    
    def write(self, name, guid, value):
        raise NotImplementedError
    
    @classmethod
    def get_instance(cls):
        if platform.system() == 'Windows':
            return WinApiEfiVariables()
        elif platform.system() == 'Linux':
            return SysfsEfiVariables()
        else:
            raise Exception("Unknown or unsupported operating system.")

class SysfsEfiVariables(EfiVariables):
    """EFI variable access for all platforms supporting /sys/firmware/efi/vars, e.g. Linux via efi_vars"""

    sysfs_efi_vars_dir = '/sys/firmware/efi/vars'
    
    def read(self, name, guid):
        assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", guid)
        filename = self.sysfs_efi_vars_dir + "/%s-%s/data" % (name, guid)
        if not os.path.exists(filename):
            # variable not found
            return None
        return file(filename).read()

    def available(self):
        return os.path.isdir(self.sysfs_efi_vars_dir)
        
    def __iter__(self):
        if os.path.isdir(self.sysfs_efi_vars_dir):
            for filename in os.listdir(self.sysfs_efi_vars_dir):
                if filename == '.' or filename == '..':
                    continue
                else:
                    if os.path.isdir(self.sysfs_efi_vars_dir + '/' + filename):
                        yield filename
        else:
            raise StopIteration

    def __getitem__(self, key):
        filename = self.sysfs_efi_vars_dir + "/%s-%s/data" % key
        if not os.path.exists(filename):
            # variable not found
            return None
        return file(filename).read()

    
class WinApiEfiVariables(EfiVariables):
    """EFI variable access for Windows platforms"""
    
    def __init__(self):
        # enable required SeSystemEnvironmentPrivilege privilege
        privilege = win32security.LookupPrivilegeValue(None, 'SeSystemEnvironmentPrivilege')
        token = win32security.OpenProcessToken(win32process.GetCurrentProcess(), win32security.TOKEN_READ|win32security.TOKEN_ADJUST_PRIVILEGES)
        win32security.AdjustTokenPrivileges(token, False, [(privilege, win32security.SE_PRIVILEGE_ENABLED)])
        win32api.CloseHandle(token)
        
        # import firmware variable API
        self.GetFirmwareEnvironmentVariable = ctypes.windll.kernel32.GetFirmwareEnvironmentVariableW
        self.GetFirmwareEnvironmentVariable.restype = ctypes.c_int
        self.GetFirmwareEnvironmentVariable.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_int]
    
    def read(self, name, guid):
        buffer = ctypes.create_string_buffer(32768)
        length = self.GetFirmwareEnvironmentVariable(name, "{%s}" % guid, buffer, 32768)
        if length == 0:
            # FIXME: don't always raise WinError
            raise ctypes.WinError()
        return buffer[:length]
        
    def available(self):
        return True if self.GetFirmwareEnvironmentVariable is not None else False
        
    def __iter__(self):
        return None
 
    def __getitem__(self, key):
        return None
