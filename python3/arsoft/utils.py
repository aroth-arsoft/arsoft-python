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
import tempfile
from pwd import getpwnam
from grp import getgrnam

(python_major, python_minor, python_micro, python_releaselevel, python_serial) = sys.version_info
platform_is_windows = True if platform.system() == 'Windows' else False
python_is_version3 = True if python_major == 3 else False
python_is_version2 = True if python_major == 2 else False

def isRoot():
    euid = os.geteuid()
    return True if euid == 0 else False

def runcmd(args=[], verbose=False, stdin=None, input=None, executable=None, cwd=None, env=None):
    if verbose:
        print("runcmd " + ' '.join(args) + (('< ' + stdin.name) if stdin is not None else ''))
    if stdin is not None:
        stdin_param = stdin
    else:
        stdin_param = subprocess.PIPE
    p = subprocess.Popen(args, executable=executable, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin_param, shell=False, cwd=cwd, env=env)
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


def runcmdAndGetData(args=[], script=None, verbose=False, outputStdErr=False, outputStdOut=False,
                     executable=None, shell='/bin/sh',
                     stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None, cwd=None, env=None):

    script_tmpfile = None
    if script is None:
        if args:
            all_args = args
        else:
            raise ValueError('neither commandline nor script specified.')
    else:
        try:
            script_tmpfile = tempfile.NamedTemporaryFile()
            script_tmpfile.write(script.encode())
        except IOError:
            script_tmpfile = None

        all_args = [str(shell)]
        all_args.append(script_tmpfile.name)

    if input is not None:
        stdin_param = subprocess.PIPE
    else:
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
        print("runcmd " + ' '.join(all_args) +
                ' 0<%s 1>%s 2>%s' % (stdin_param, stdout_param, stderr_param)
                    )

    p = subprocess.Popen(all_args, executable=executable, stdout=stdout_param, stderr=stderr_param, stdin=stdin_param, shell=False, cwd=cwd, env=env)
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

def _is_quoted(s, quote_chars = '\'"'):
    if not isinstance(s, str):
        return False
    l = len(s)
    return True if l >= 2 and s[0] in quote_chars and s[-1] in quote_chars else False

def to_commandline(args, posix=True, env=None, quote_char='\''):
    ret = ''
    if env:
        for (env_key, env_value) in env.items():
            if ret:
                ret += ' '
            ret = ret + '%s=%s%s%s' % (env_key, quote_char, env_value, quote_char)
    for arg in args:
        if ret:
            ret += ' '
        if not _is_quoted(arg):
            ret = ret + '%s%s%s' % (quote_char, arg, quote_char)
        else:
            ret = ret + arg
    return ret

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
    ret = False
    if os.path.isfile(pidfile):
        try:
            f = open(pidfile, 'r')
            pid = int(f.readline())
            f.close()
        except IOError:
            pid = None
        if pid is not None:
            ret = isProcessRunning(pid)
    return ret

def readPIDFromPIDFile(pidfile):
    ret = None
    if os.path.isfile(pidfile):
        try:
            f = open(pidfile, 'r')
            ret = int(f.readline())
            f.close()
        except IOError:
            pass
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

def which(name, flags=os.X_OK, only_first=False):
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
        if only_first:
            return None
        else:
            return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    if only_first:
        return result[0] if result else None
    else:
        return result

def import_non_local(name, custom_name=None):
    import imp, sys

    custom_name = custom_name or name

    f, pathname, desc = imp.find_module(name, sys.path[1:])
    module = imp.load_module(custom_name, f, pathname, desc)
    f.close()

    return module

def detect_file_type(filename, fallback=None):
    try:
        import magic
        ms = magic.open(magic.NONE)
        ms.load()
    except ImportError:
        ms = None
    file_type = None
    if ms is not None:
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

class log_collector(object):
    def __init__(self, data=None):
        self.data = [] if not data else data

    def __call__(self, line):
        self.data.append(line)

    def __str__(self):
        return '\n'.join(self.data)

class logfile_writer_proxy(object):
    def __init__(self, writer, prefix=None, add_timestamp=True):
        self._writer = writer
        self._prefix = prefix
        self._add_timestamp = True
        self._notifiers = []

    def current_timestamp(self, timestamp=None):
        if timestamp is None:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.fromtimestamp(timestamp)
        return now.strftime("%Y-%m-%d %H:%M:%S.%f")

    def add_notify(self, fun):
        self._notifiers.append(fun)

    def remove_notify(self, fun):
        try:
            self._notifiers.remove(fun)
        except ValueError:
            pass
        except AttributeError:
            pass

    def __call__(self, line):
        self._write_line(line)

    def write(self, *args):
        self._write_line('\t'.join(args))

    def _write_line(self, line):
        add_newline = True if line and line[-1] != '\n' else False
        if self._prefix:
            full = self._prefix + line
        else:
            full = line
        if add_newline:
            full = full + '\n'
        if self._add_timestamp:
            msg = self.current_timestamp() + '\t' + full
        else:
            msg = full
        self._writer.write(msg)
        for n in self._notifiers:
            n(msg)

def hexstring(buf):
    return ' '.join(x.encode('hex') for x in buf)

def hexstring_with_length(buf):
    return ' '.join(x.encode('hex') for x in buf) + ' - %i' % len(buf)

