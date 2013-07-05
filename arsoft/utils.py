#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os, stat, shutil
import pwd
import grp
import subprocess
import sys
import platform
from pwd import getpwnam
from grp import getgrnam

(python_major, python_minor, python_micro, python_releaselevel, python_serial) = sys.version_info
platform_is_windows = True if platform.system() == 'Windows' else False

def isRoot():
    euid = os.geteuid()
    return True if euid == 0 else False

def runcmd(exe, args=[], verbose=False, stdin=None, input=None, cwd=None, env=None):
    all_args = [str(exe)]
    all_args.extend(args)
    if verbose:
        print("runcmd " + ' '.join(all_args) + (('< ' + stdin.name) if stdin is not None else ''))
    if stdin is not None:
        stdin_param = stdin
    else:
        stdin_param = subprocess.PIPE
    p = subprocess.Popen(all_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin_param, shell=False, cwd=cwd, env=env)
    if p:
        (stdoutdata, stderrdata) = p.communicate(input)
        if stdoutdata is not None:
            if int(python_major) < 3: # check for version < 3
                sys.stdout.write(stdoutdata)
                sys.stdout.flush()
            else:
                sys.stdout.buffer.write(stdoutdata)
                sys.stdout.buffer.flush()
        if stderrdata is not None:
            if int(python_major) < 3: # check for version < 3
                sys.stderr.write(stderrdata)
                sys.stderr.flush()
            else:
                sys.stderr.buffer.write(stderrdata)
                sys.stderr.buffer.flush()
        sts = p.returncode
    else:
        sts = -1
    return sts


def runcmdAndGetData(exe, args=[], verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, input=None, cwd=None, env=None):
    all_args = [str(exe)]
    all_args.extend(args)
    if verbose:
        print("runcmd " + ' '.join(all_args) + (('< ' + stdin.name) if stdin is not None else ''))
    
    stdin_param = stdin if stdin is not None else subprocess.PIPE
    stdout_param = stdout if stdout is not None else subprocess.PIPE
    stderr_param = stderr if stderr is not None else subprocess.PIPE
    p = subprocess.Popen(all_args, stdout=stdout_param, stderr=stderr_param, stdin=stdin_param, shell=False, cwd=cwd, env=env)
    if p:
        (stdoutdata, stderrdata) = p.communicate(input)
        if stdoutdata is not None and outputStdOut:
            if int(python_major) < 3: # check for version < 3
                sys.stdout.write(stdoutdata)
                sys.stdout.flush()
            else:
                sys.stdout.buffer.write(stdoutdata)
                sys.stdout.buffer.flush()
        if stderrdata is not None and outputStdErr:
            if int(python_major) < 3: # check for version < 3
                sys.stderr.write(stderrdata)
                sys.stderr.flush()
            else:
                sys.stderr.buffer.write(stderrdata)
                sys.stderr.buffer.flush()
        sts = p.returncode
    else:
        sts = -1
        stdoutdata = None
        stderrdata = None
    return (sts, stdoutdata, stderrdata)


def rmtree(directory):
    def remove_readonly(fn, path, excinfo):
        if fn is os.rmdir:
            os.chmod(path, stat.S_IWRITE)
            os.rmdir(path)
        elif fn is os.remove:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

    shutil.rmtree(directory, onerror=remove_readonly)

def isProcessRunning(pid, use_kill=False):
    '''Check For the existence of a unix pid.
    '''
    if use_kill:
        try:
            os.kill(pid, 0)
        except OSError as e:
            return False
        return True
    else:
        return os.path.isdir('/proc/' + str(pid))

def isProcessRunningByPIDFile(pidfile):
    if os.path.isfile(pidfile):
        try:
            f = open(pidfile, 'r')
            pid = int(f.readline())
            f.close()
        except IOError:
            pid = None
        if pid is not None:
            ret = isProcessRunning(pid)
        else:
            ret = False
    else:
        ret = False
    return ret
        

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(077)
    return True

def isMountDirectory(path):
    return os.path.ismount(path)

def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def is_localhost(hostname):
    if hostname == 'localhost' or hostname == 'loopback' or hostname == '127.0.0.1' or hostname == '::1':
        return True
    else:
        return False

def enum(**enums):
    return type('Enum', (), enums)

def get_main_script_filename():
    import __main__
    return os.path.realpath(os.path.abspath(__main__.__file__))

def to_uid(user):
    try:
        uid = int(user)
    except ValueError:
        uid = getpwnam(user).pw_uid
    return uid

def to_gid(group):
    try:
        gid = int(group)
    except ValueError:
        gid = getgrnam(group).gr_gid
    return gid

# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Utilities for dealing with processes.
"""

def which(name, flags=os.X_OK):
    """Search PATH for executable files with the given name.
    
    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.
    
    @type name: C{str}
    @param name: The name for which to search.
    
    @type flags: C{int}
    @param flags: Arguments to L{os.access}.
    
    @rtype: C{list}
    @param: A list of the full paths to files found, in the
    order in which they were found.
    """
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result

def import_non_local(name, custom_name=None):
    import imp, sys

    custom_name = custom_name or name

    f, pathname, desc = imp.find_module(name, sys.path[1:])
    module = imp.load_module(custom_name, f, pathname, desc)
    f.close()

    return module

def detect_file_type(filename):
    import magic
    ms = magic.open(magic.NONE)
    ms.load()
    file_type = None
    if hasattr(filename, 'read'):
        try:
            buf = filename.read(256)
            if hasattr(filename, 'seek'):
                filename.seek(-len(buf),1)
            file_type = ms.buffer(buf)
        except IOError:
            file_type = None
    else:
        file_type = ms.file(filename)
    return file_type
