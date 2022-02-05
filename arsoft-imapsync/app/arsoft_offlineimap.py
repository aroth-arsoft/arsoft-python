#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os.path
import collections

from inifile import IniFile
import socket
import subprocess
import platform
import datetime

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

def runcmdAndGetData(args=[], script=None, verbose=False, outputStdErr=False, outputStdOut=False,
                     executable=None, shell='/bin/sh',
                     stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None, cwd=None, env=None,
                     runAsUser=None, su='/bin/su'):

    script_tmpfile = None
    if script is None:
        if args:
            if runAsUser is None:
                all_args = args
            else:
                all_args = [su, '-s', shell, '-', str(runAsUser), '-c', ' '.join(args)]
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

def gethostname_tuple(fqdn=None):
    if fqdn is None:
        fqdn = socket.getfqdn().lower()
    else:
        fqdn = fqdn.lower()
    if '.' in fqdn:
        (hostname, domain) = fqdn.split('.', 1)
    else:
        hostname = fqdn
        domain = 'localdomain'
    return (fqdn, hostname, domain)

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

class OfflineImap(object):

    DEFAULT_IMAP_PORT = 143

    class Repository(object):
        def __init__(self, username=None, password=None,
                     master_username=None,
                     master_password=None,
                     server=None, port=None, server_type=None, ssl=True, mechanisms=None,
                     maildir=None,
                     readonly=False,
                     gssapi=False,
                     excluded_folders=['backup/', 'shared/'],
                     separator=None ):
            self.username = username
            self.password = password
            self.master_username = master_username
            self.master_password = master_password
            self.server = server
            self.port = int(port) if port else None
            self.server_type = server_type.lower() if server_type is not None else None
            self.ssl = ssl
            if mechanisms is None:
                self.mechanisms = ['XOAUTH2', 'CRAM-MD5', 'PLAIN', 'LOGIN']
                if gssapi:
                    self.mechanisms += ['GSSAPI']
            else:
                self.mechanisms = mechanisms
            self.readonly = readonly
            self.excluded_folders = excluded_folders
            self.maildir = maildir
            self.separator = separator

        @property
        def is_valid(self):
            if self.server_type == 'maildir':
                return True if self.maildir is not None or self.username is not None else False
            else:
                return self.username is not None and self.server is not None

        @property
        def domain(self):
            idx = self.username.find('@')
            if idx > 0:
                return self.username[idx+1:]
            else:
                return None

        @property
        def user(self):
            idx = self.username.find('@')
            if idx > 0:
                return self.username[0:idx]
            else:
                return self.username

        def config(self, base_dir):
            if self.server_type == 'maildir':
                items = collections.OrderedDict( { 'type': 'Maildir' } )
                if self.maildir is not None:
                    items['localfolders'] = os.path.join(base_dir, self.maildir)
                else:
                    items['localfolders'] = os.path.join(base_dir, self.username)
                items['sep'] = '/'
            else:
                if self.server_type == 'gmail':
                    items = collections.OrderedDict( { 'type': 'Gmail' } )
                else:
                    items = collections.OrderedDict( { 'type': 'IMAP' } )
                if self.separator is not None:
                    items['sep'] = self.separator
                items['remotehost'] = self.server
                items['remoteuser'] = self.username
                items['remotepass'] = self.password
                port = OfflineImap.DEFAULT_IMAP_PORT if self.port is None else self.port
                if self.port is not None:
                    items['remoteport'] = port
                if self.master_username is not None:
                    if self.server_type == 'dovecot':
                        items['remoteuser'] = '%s*%s' % (self.username, self.master_username)
                        items['remotepass'] = self.master_password
                    elif self.server_type == 'cyrus':
                        items['remoteuser'] = self.master_username
                        items['remote_identity'] = self.username
                        items['remotepass'] = self.master_password
                    else:
                        items['remoteuser'] = self.username
                if self.mechanisms is not None:
                    if isinstance(self.mechanisms, str):
                        items['auth_mechanisms'] = self.mechanisms
                    else:
                        items['auth_mechanisms'] = ','.join(self.mechanisms)
                if port == 143:
                    items['ssl'] = 'no'
                else:
                    items['ssl'] = 'yes' if self.ssl else 'no'
                if self.ssl:
                    items['sslcacertfile'] = '/etc/ssl/certs/ca-certificates.crt'
                    items['tls_level'] = 'tls_no_ssl'
                    items['ssl_version'] = 'tls1_2'
                if port == 143:
                    items['starttls'] = 'yes' if self.ssl else 'no'
                else:
                    items['starttls'] = 'no'

            items['readonly'] = 'True' if self.readonly else 'False'
            # DO NOT backup the backups
            if self.excluded_folders:
                expr = []
                for f in self.excluded_folders:
                    expr.append('not folder.startswith(\'%s\')' % f)
                items['folderfilter'] = expr = 'lambda folder: ' + ' and '.join(expr)
            if self.server_type == 'cyrus':
                items['nametrans'] = 'lambda foldername: re.sub(\'^INBOX/\', \'\', foldername)'

            ret = ''
            for k,v in items.items():
                ret += '%s = %s\n' % (k,v)
            return ret

        def __str__(self):
            if self.maildir is not None:
                return 'maildir:%s' % self.maildir
            else:
                return '%s on %s' % (self.username, self.server)

    class AccountItem(object):
        def __init__(self, enabled, name, remote, local):
            self.name = name
            self.enabled = enabled
            self.remote = OfflineImap.Repository(**remote)
            self.local = OfflineImap.Repository(**local)

        def __str__(self):
            return '%s (%s -> %s)' % (self.name, self.remote, self.local)

        def local_config(self, base_dir):
            return self.local.config(base_dir)

        def remote_config(self, base_dir):
            return self.remote.config(base_dir)

        @property
        def is_valid(self):
            return self.name is not None and self.local.is_valid and self.remote.is_valid

        @property
        def config_file(self):
            return '%s.conf' % self.name

        @property
        def metadata_dir(self):
            return 'meta-%s' % self.name

        def write_config(self, directory):
            if directory is None or not self.is_valid:
                return None
            ret = None
            filename = os.path.join(directory, self.config_file)
            metadata_dir = os.path.join(directory, self.metadata_dir)
            try:
                f = open(filename, 'w')
                f.write("""[general]
accounts = %(accountname)s
metadata = %(metadata_dir)s

[Account %(accountname)s]
localrepository = %(accountname)s-local
remoterepository = %(accountname)s-remote

[Repository %(accountname)s-local]
%(local_config)s
[Repository %(accountname)s-remote]
%(remote_config)s
""" % {                 'accountname': self.name,
                        'metadata_dir': metadata_dir,
                        'remote_config': self.remote_config(directory),
                        'local_config': self.local_config(directory),
                        } )
                f.close()
                ret = filename
            except IOError as e:
                pass
            return ret

        def logfile(self, directory):
            if directory is None or not self.is_valid:
                return None
            return os.path.join(directory, self.name + '.log')

    class Session(object):
        def __init__(self, logfile, verbose=False):
            self.logfile = logfile
            self._verbose = verbose
            self._logfile_fobj = None
            self._logfile_proxy = None

        def __del__(self):
            self.closelog()

        def closelog(self):
            if self._logfile_fobj is not None:
                self._logfile_fobj.close()

        def openlog(self):
            if self._logfile_fobj is None:
                try:
                    self._logfile_fobj = open(self.logfile, 'w')
                except IOError as e:
                    self._logfile_fobj = None
                if self._logfile_fobj:
                    self._logfile_proxy = logfile_writer_proxy(self._logfile_fobj)
            return self._logfile_proxy

        def writelog(self, *args):
            proxy = self.openlog()
            if proxy:
                proxy.write(*args)
            if self._verbose:
                sys.stdout.write(' '.join(args) + '\n')

        @property
        def logfile_proxy(self):
            if self._logfile_proxy is None and self.logfile is not None:
                self.openlog()
            return self._logfile_proxy

    def __init__(self, offlineimap_exe=None, private_dir=None, verbose=False, dryrun=False):
        self._account_list = None
        self._private_dir = private_dir
        if offlineimap_exe is None:
            self.offlineimap_exe = which('offlineimap', only_first=True)
        else:
            p = os.path.abspath(offlineimap_exe)
            if os.path.isfile(p):
                self.offlineimap_exe = p
        self._verbose = verbose
        self._dryrun = dryrun
        (fqdn, hostname, domain) = gethostname_tuple()
        self.fqdn = fqdn
        self.hostname = hostname
        self.config_file = None
        self.logfile = os.path.join(self._private_dir, 'log') if self._private_dir else None
        self._session = OfflineImap.Session(logfile=self.logfile, verbose=verbose)

    @property
    def is_installed(self):
        return True if self.offlineimap_exe is not None else False

    def add_account(self, account):
        if not account.is_valid:
            return False
        if self._account_list is None:
            self._account_list = []
        self._account_list.append(account)
        return True

    def readConfig(self, filename):
        if isinstance(filename, str):
            inifile = IniFile(commentPrefix='#', keyValueSeperator='=', disabled_values=False)
            ret = inifile.open(filename)
        else:
            inifile = filename
            ret = True
        if ret:
            ret = self._read_conf(inifile)
        return ret

    def _read_conf(self, inifile):
        if inifile is None:
            return False
        self._account_list = []
        self.remote_master_password = inifile.get(None, 'remote_master_password', None)
        if self.remote_master_password is not None:
            self.remote_master_username = inifile.get(None, 'remote_master_username', 'doveadm')
        else:
            self.remote_master_username = None
        self.local_master_password = inifile.get(None, 'local_master_password', None)
        if self.local_master_password is not None:
            self.local_master_username = inifile.get(None, 'local_master_username', 'doveadm')
        else:
            self.local_master_username = None
        self.default_remote_server = inifile.get(None, 'remote_server', self.fqdn)
        self.default_remote_port = inifile.get(None, 'remote_port', 143)
        self.default_remote_server_type = inifile.get(None, 'remote_server_type', 'dovecot')
        self.default_local_server = inifile.get(None, 'local_server', self.fqdn)
        self.default_local_port = inifile.get(None, 'local_port', 143)
        self.default_local_server_type = inifile.get(None, 'local_server_type', 'dovecot')
        for sect in inifile.sections:
            if sect is None:
                continue
            enabled = inifile.get(sect, 'enabled', True)
            remote_username = inifile.get(sect, 'remote_username', None)
            remote_password = inifile.get(sect, 'remote_password', None)
            remote_server = inifile.get(sect, 'remote_server', self.default_remote_server)
            remote_port = inifile.get(sect, 'remote_port', self.default_remote_port)
            remote_server_type = inifile.get(sect, 'remote_server_type', self.default_remote_server_type)
            remote_maildir = inifile.get(sect, 'remote_maildir', None)
            remote_readonly = inifile.get(sect, 'remote_readonly', True)
            local_username = inifile.get(sect, 'local_username', None)
            local_password = inifile.get(sect, 'local_password', None)
            local_server = inifile.get(sect, 'local_server', self.default_local_server)
            local_port = inifile.get(sect, 'local_port', self.default_local_port)
            local_server_type = inifile.get(sect, 'local_server_type', self.default_local_server_type)
            local_maildir = inifile.get(sect, 'local_maildir', None)
            local_readonly = inifile.get(sect, 'local_readonly', False)

            remote = {}
            remote['username'] = remote_username
            remote['password'] = remote_password
            remote['server'] = remote_server
            remote['port'] = remote_port
            remote['server_type'] = remote_server_type
            remote['master_password'] = self.remote_master_password
            remote['master_username'] = self.remote_master_username
            remote['maildir'] = remote_maildir
            remote['readonly'] = remote_readonly

            local = {}
            local['username'] = local_username
            local['password'] = local_password
            local['server'] = local_server
            local['port'] = local_port
            local['server_type'] = local_server_type
            local['master_password'] = self.local_master_password
            local['master_username'] = self.local_master_username
            local['maildir'] = local_maildir
            local['readonly'] = local_readonly

            account = OfflineImap.AccountItem(
                enabled=enabled,
                name=sect,
                local=local,
                remote=remote
                )
            if account.is_valid:
                self._account_list.append(account)
            elif self._verbose:
                print('account %s not valid' % account)
        return True

    @property
    def account_list(self):
        return self._account_list

    @account_list.setter
    def account_list(self, value):
        self._account_list = value

    def _write_account_config(self, account=None, base_dir=None):
        if base_dir is None:
            base_dir = self._private_dir
        return account.write_config(directory=base_dir)

    def _sync_account(self, account=None, base_dir=None, log=None, session=None):
        config_file = self._write_account_config(account=account, base_dir=base_dir)
        if not config_file:
            return False
        args=[self.offlineimap_exe]
        if self._dryrun:
            args.append('--dry-run')
        args.extend(['-c', config_file])
        if log is None and session is not None:
            log=session.logfile_proxy
        #print('_sync_account log=%s' % log)
        (sts, stdout_data, stderr_data) = runcmdAndGetData(args, stdout=log, stderr=None,
                                                           outputStdErr=False, outputStdOut=False,
                                                           stderr_to_stdout=True,
                                                           verbose=self._verbose)
        return True if sts == 0 else False

    def _run_account(self, account=None, base_dir=None, log=None, per_account_log=False):
        if per_account_log and log is None:
            logfile = account.logfile(base_dir)
            account_session = OfflineImap.Session(logfile)
        else:
            logfile = None
            account_session = self._session
        #print('per_account_log %s, log %s, %s' % (per_account_log, log, account_session))
        ok = self._sync_account(account=account, base_dir=base_dir, log=log, session=account_session)

        if per_account_log and log is None:
            account_session.closelog()
        return (ok, logfile if log is None else log)

    def run(self, account=None, base_dir=None, log=None, per_account_log=False):
        if base_dir is None:
            base_dir = self._private_dir
        if account is None:
            ret = []
            if self._account_list is not None:
                for account in self._account_list:
                    (ok, logfile) = self._run_account(account=account, base_dir=base_dir, log=log, per_account_log=per_account_log)
                    ret.append( (account, ok, logfile) )
        else:
            ret = self._run_account(account=account, base_dir=base_dir, log=log, per_account_log=per_account_log)
        return ret

    def write_config(self, account=None, base_dir=None):
        ok = True
        ret = []
        if account is None:
            for account in self._account_list:
                config_file = self._write_account_config(account=account, base_dir=base_dir)
                if not config_file:
                    ok = False
                else:
                    ret.append(config_file)
        else:
            config_file = self._write_account_config(account=account, base_dir=base_dir)
            if not config_file:
                ok = False
            else:
                ret.append(config_file)

        return ret if ok else None
