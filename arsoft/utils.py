#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os, stat, shutil
import pwd
import grp
import subprocess
import sys
import platform
import datetime
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
        print(("runcmd " + ' '.join(all_args) + (('< ' + stdin.name) if stdin is not None else '')))
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


def runcmdAndGetData(exe, args=[], verbose=False, outputStdErr=False, outputStdOut=False,
                     stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None, cwd=None, env=None):
    all_args = [str(exe)]
    all_args.extend(args)
    
    stdin_param = stdin if stdin is not None else subprocess.PIPE
    if stdout is not None and hasattr(stdout, '__call__'):
        stdout_param = subprocess.PIPE
    else:
        stdout_param = stdout if stdout is not None else subprocess.PIPE
    if stderr_to_stdout:
        stderr_param = subprocess.STDOUT
    else:
        if stdout is not None and hasattr(stdout, '__call__'):
            stderr_param = subprocess.PIPE
        else:
            stderr_param = stdout if stdout is not None else subprocess.PIPE
    if verbose:
        print(("runcmd " + ' '.join(all_args) +
                ' <' + str(stdin_param) +
                ' 1>' + str(stdout_param) +
                ' 2>' + str(stderr_param)
                    ))

    p = subprocess.Popen(all_args, stdout=stdout_param, stderr=stderr_param, stdin=stdin_param, shell=False, cwd=cwd, env=env)
    if p:
        if stdout is not None and hasattr(stdout, '__call__'):
            encoding = 'CP1252' if platform.system() == 'Windows' else 'utf-8'
            while True:
                line = ""
                try:
                    line = p.stdout.readline()
                except Exception:
                    pass
                try:
                    line = line.decode(encoding)
                except:
                    continue
                if not line:
                    break
                line = line.rstrip('\n\r')
                stdout(line)
            sts = p.wait()
            stdoutdata = None
            stderrdata = None
        else:
            if input:
                (stdoutdata, stderrdata) = p.communicate(input.encode())
            else:
                (stdoutdata, stderrdata) = p.communicate()
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
    old_umask = os.umask(0o77)
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

def replace_invalid_chars(str, invalid_chars=['\r', '\n', '\t', ' ', ':', '@'], replacement='_'):
    ret = ''
    idx = 0
    l = len(str)
    while idx < l:
        if str[idx] in invalid_chars:
            ret += replacement
        else:
            ret += str[idx]
        idx += 1
    return ret

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
    exts = [_f for _f in os.environ.get('PATHEXT', '').split(os.pathsep) if _f]
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

def detect_file_type(filename, fallback=None):
    import magic
    ms = magic.open(magic.NONE)
    ms.load()
    file_type = None
    if hasattr(filename, 'read'):
        try:
            buf = filename.read(256)
            #if hasattr(filename, 'seek'):
            #    filename.seek(-len(buf),1)
            file_type = ms.buffer(buf)
        except IOError as e:
            print(e)
            file_type = None
        print(file_type)
    else:
        file_type = ms.file(filename)
    if file_type is None:
        file_type = fallback
    return file_type

def is_quoted_string(str):
    if len(str) > 1 and ((str[0] == '"' and str[-1] == '"') or (str[0] == '\'' and str[-1] == '\'')):
        return True
    else:
        return False

def unquote_string(str):
    if is_quoted_string(str):
        return str[1:-1]
    else:
        return str

def quote_string(str, quote_char='\''):
    return quote_char + str + quote_char

def getlogin():
    """:return: string identifying the currently active system user as name@node
    :note: user can be set with the 'USER' environment variable, usually set on windows
    :note: on unix based systems you can use the password database
    to get the login name of the effective process user"""
    if os.name == "posix":
        username = pwd.getpwuid(os.geteuid()).pw_name
    else:
        ukn = 'UNKNOWN'
        username = os.environ.get('USER', os.environ.get('USERNAME', ukn))
        if username == ukn and hasattr(os, 'getlogin'):
            username = os.getlogin()
    return username

class logfile_writer_proxy(object):
    def __init__(self, writer, prefix=None, add_timestamp=True):
        self._writer = writer
        self._prefix = prefix
        self._add_timestamp = True

    def current_timestamp(self, timestamp=None):
        if timestamp is None:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.fromtimestamp(timestamp)
        return now.strftime("%Y-%m-%d %H:%M:%S.%f")

    def __call__(self, line):
        self._write_line(line)

    def write(self, *args):
        self._write_line('\t'.join(args))

    def _write_line(self, line):
        if self._prefix:
            full = self._prefix + line + '\n'
        else:
            full = line + '\n'
        if self._add_timestamp:
            self._writer.write(self.current_timestamp() + '\t' + full)
        else:
            self._writer.write(full)
