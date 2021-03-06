#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from .utils import runcmdAndGetData, to_commandline, platform_is_windows, python_is_version3, which, isRoot
from .socket_utils import gethostname
import sys
import tempfile
import os.path
import copy, uuid

def _find_executable_impl(user_override, ssh_name, putty_name):
    if user_override:
        if os.access(user_override, os.X_OK):
            exec_path = os.path.abspath(user_override)
            exec_basename, exec_basename_ext = os.path.splitext(os.path.basename(exec_path).lower())
            exec_putty = True if exec_basename == putty_name else False
        else:
            exec_path = None
            exec_putty = False
    else:
        if platform_is_windows:
            exec_path = which(putty_name + '.exe', only_first=True)
            exec_putty = True
        else:
            exec_path = which(ssh_name, only_first=True)
            exec_putty = False
    return (exec_path, exec_putty)

def _find_ssh_executable(ssh=None):
    return _find_executable_impl(ssh, ssh_name='ssh', putty_name='putty')

def _find_ssh_keygen_executable(ssh_keygen=None):
    return _find_executable_impl(ssh_keygen, ssh_name='ssh-keygen', putty_name='puttygen')

def _find_ssh_copy_id_executable(ssh_copy_id=None):
    return _find_executable_impl(ssh_copy_id, ssh_name='ssh-copy-id', putty_name='puttygen')

def _find_scp_executable(scp=None):
    return _find_executable_impl(scp, ssh_name='scp', putty_name='plink')

(SSH_EXECUTABLE, SSH_USE_PUTTY) = _find_ssh_executable()
(SSH_KEYGEN_EXECUTABLE, SSH_KEYGEN_USE_PUTTY) = _find_ssh_keygen_executable()
(SSH_COPY_ID_EXECUTABLE, SSH_COPY_ID_USE_PUTTY) = _find_ssh_copy_id_executable()
(SCP_EXECUTABLE, SCP_USE_PUTTY) = _find_scp_executable()

def ssh_runcmdAndGetData(server, args=[], script=None, keyfile=None, username=None, password=None,
                         sudo_command=None, sudo_env=None, shell='/bin/sh',
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         stderr_to_stdout=False,
                         ssh_env=None, ssh_verbose=0,
                         allocateTerminal=False, x11Forwarding=False, quote_char='\'',
                         ssh_executable=SSH_EXECUTABLE, use_putty=SSH_USE_PUTTY):

    if use_putty:
        ssh_args = [ssh_executable, '-batch', '-noagent', '-a', '-x']
        if keyfile is None and password:
            ssh_args.extend(['-pw', password])
    else:
        ssh_args = [ssh_executable, '-a', '-o', 'BatchMode=yes']

    while ssh_verbose > 0:
        ssh_args.append('-v')
        ssh_verbose = ssh_verbose - 1

    if username:
        ssh_args.extend(['-l', username ])
    if keyfile:
        if isinstance(keyfile, SSHSessionKey):
            ssh_args.extend(['-i', keyfile.keyfile])
        else:
            ssh_args.extend(['-i', keyfile])

    if not use_putty:
        ssh_args.append( '-t' if allocateTerminal else '-T')
        ssh_args.append( '-X' if x11Forwarding else '-x')

    ssh_args.append(server)
    sudo_env_str = ''
    if sudo_command and sudo_env:
        for (env_key, env_value) in sudo_env.items():
            sudo_env_str = sudo_env_str + '%s=\'%s\'' % (env_key, env_value)
    env_str = ''
    if env:
        for (env_key, env_value) in env.items():
            env_str = env_str + '%s=\'%s\'' % (env_key, env_value)
        env_str = env_str + ' '

    if script is None:
        if isinstance(args, str):
            commandline = env_str + to_commandline([args], quote_char=quote_char)
        else:
            commandline = env_str + to_commandline(args, quote_char=quote_char)
        if sudo_command:
            ssh_args.append('%s %s %s' % (sudo_env_str, sudo_command, commandline))
        else:
            ssh_args.append(commandline)
        input = None
        return runcmdAndGetData(ssh_args,
                                verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                stderr_to_stdout=stderr_to_stdout,
                                stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=ssh_env)

    else:
        tmpfile = '/tmp/arsoft_remote_ssh_%s.sh' % uuid.uuid4()
        put_args = copy.deepcopy(ssh_args)
        # do not allow anyone except ourself to execute (read/write) this script
        put_args.append('umask 077; /bin/cat > ' + tmpfile)
        cleanup_args = copy.deepcopy(ssh_args)
        cleanup_args.append('/bin/rm -f ' + tmpfile)
        exec_args = copy.deepcopy(ssh_args)
        if isinstance(args, str):
            script_args = args
        else:
            script_args = ' '.join(args) if args else ''
        if sudo_command:
            exec_args.append('%s %s %s%s %s %s' % (sudo_env_str, sudo_command, env_str, shell, tmpfile, script_args))
        else:
            exec_args.append('%s%s %s %s' % (env_str, shell, tmpfile, script_args))

        # convert any M$-newlines into the real-ones
        real_script = script.replace('\r\n', '\n')

        (put_sts, put_stdout, put_stderr) = runcmdAndGetData(put_args, input=real_script,
                                verbose=verbose, cwd=cwd, env=ssh_env)

        if put_sts == 0:
            if verbose:
                print(real_script)
            (sts, stdout_data, stderr_data) = runcmdAndGetData(exec_args,
                                verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                stderr_to_stdout=stderr_to_stdout,
                                stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=ssh_env)
        else:
            (sts, stdout_data, stderr_data) = (put_sts, put_stdout, put_stderr)

        (cleanup_sts, cleanup_stdout, cleanup_stderr) = runcmdAndGetData(cleanup_args,
                                verbose=verbose, cwd=cwd, env=ssh_env)
        return (sts, stdout_data, stderr_data)

def scp(server, files, target_dir, keyfile=None, username=None, password=None, 
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         scp_executable=SCP_EXECUTABLE, use_putty=SCP_USE_PUTTY):

    if use_putty:
        args = [scp_executable, '-batch', '-noagent', '-q', '-l']
        if username:
            args.extend(['-l', username ])
        if keyfile is None and password:
            args.extend(['-pw', password])
    else:
        # enable batch-mode, compression and quiet (no progress)
        args = [scp_executable, '-B', '-C', '-q']

    if keyfile:
        if isinstance(keyfile, SSHSessionKey):
            args.extend(['-i', keyfile.keyfile])
        else:
            args.extend(['-i', keyfile])

    args.extend(files)
    if use_putty or username is None:
        args.append(server + ':' + target_dir)
    else:
        args.append(username + '@' + server + ':' + target_dir)

    return runcmdAndGetData(args, input=None,
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
 

def ssh_keygen(dest_filename, password=None, comment=None, keytype='rsa',
                     verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                     ssh_keygen_executable=SSH_KEYGEN_EXECUTABLE, use_putty=SSH_KEYGEN_USE_PUTTY):
    
    if use_putty:
        args = [ssh_keygen_executable]
    else:
        args = [ssh_keygen_executable, '-t', keytype, '-f', dest_filename]
        if password is None:
            args.extend(['-N', ''])
        else:
            args.extend(['-N', password])
        if comment:
            args.extend(['-C', comment])

    (sts, stdout, stderr) = runcmdAndGetData(args, input=None,
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
    if sts == 0:
        return (dest_filename, dest_filename + '.pub')
    else:
        return (None, None)

def ssh_create_temp_file(server, data, keyfile=None, username=None, password=None,
                         sudo_command=None, sudo_env=None, shell='/bin/sh',
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         ssh_env=None, ssh_verbose=0,
                         allocateTerminal=False, x11Forwarding=False,
                         ssh_executable=SSH_EXECUTABLE, use_putty=SSH_USE_PUTTY):

    if use_putty:
        ssh_args = [ssh_executable, '-batch', '-noagent', '-a', '-x']
        if keyfile is None and password:
            ssh_args.extend(['-pw', password])
    else:
        ssh_args = [ssh_executable, '-a', '-o', 'BatchMode=yes']

    while ssh_verbose > 0:
        ssh_args.append('-v')
        ssh_verbose = ssh_verbose - 1

    if username:
        ssh_args.extend(['-l', username ])
    if keyfile:
        if isinstance(keyfile, SSHSessionKey):
            ssh_args.extend(['-i', keyfile.keyfile])
        else:
            ssh_args.extend(['-i', keyfile])

    if not use_putty:
        ssh_args.append( '-t' if allocateTerminal else '-T')
        ssh_args.append( '-X' if x11Forwarding else '-x')

    ssh_args.append(server)
    sudo_env_str = ''
    if sudo_command and sudo_env:
        for (env_key, env_value) in sudo_env.items():
            sudo_env_str = sudo_env_str + '%s=\'%s\'' % (env_key, env_value)
    env_str = ''
    if env:
        for (env_key, env_value) in env.items():
            env_str = env_str + '%s=\'%s\'' % (env_key, env_value)
        env_str = env_str + ' '

    tmpfile = '/tmp/arsoft_ssh_tmp_%s' % uuid.uuid4()
    put_args = copy.deepcopy(ssh_args)
    # do not allow anyone except ourself to execute (read/write) this script
    put_args.append('umask 077; /bin/cat > ' + tmpfile)

    (put_sts, put_stdout, put_stderr) = runcmdAndGetData(put_args, input=data,
                            verbose=verbose, cwd=cwd, env=ssh_env)
    if put_sts == 0:
        return tmpfile
    else:
        return None

def ssh_copy_id(public_keyfile, server, username=None,
                     verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                     ssh_copy_id_executable=SSH_COPY_ID_EXECUTABLE, use_putty=SSH_COPY_ID_USE_PUTTY):
    if use_putty:
        args = [ssh_copy_id_executable]
    else:
        args = [ssh_copy_id_executable, '-i', public_keyfile]
        if username:
            args.append('%s@%s' % (username, server))
        else:
            args.append(server)

    (sts, stdout, stderr) = runcmdAndGetData(args, input=None,
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
    if sts == 0:
        return True
    else:
        return False
    
class SSHUrl(object):
    def __init__(self, url=None):
        self.scheme = None
        self.username = None
        self.password = None
        self.hostname = None
        self._port = None
        self.path = None
        if url is not None:
            self.parse(url)

    def parse(self, url, scheme='ssh'):
        idx = url.find('://')
        if idx != -1:
            self.scheme = url[0:idx]
            scheme_idx = idx + 3
        else:
            self.scheme = scheme
            scheme_idx = 0
        idx = url.find('@', scheme_idx)
        if idx != -1:
            username_and_pw = url[scheme_idx:idx]
            hostname_and_port = url[idx+1:]
            idx = username_and_pw.find(':')
            if idx != -1:
                self.username = username_and_pw[0:idx]
                self.password = username_and_pw[idx+1:]
            else:
                self.username = username_and_pw
                self.password = None
            idx = hostname_and_port.find(':')
            if idx != -1:
                self.hostname = hostname_and_port[0:idx]
                self.path = hostname_and_port[idx+1:]
            else:
                self.hostname = hostname_and_port
                self.path = None
        else:
            self.username = None
            self.password = None
            idx = url.find(':', scheme_idx)
            if idx != -1:
                self.hostname = url[scheme_idx:idx]
                self.path = url[idx+1:]
            else:
                self.hostname = url
                self.path = None
        return False if self.hostname is None else True

    @property
    def port(self):
        return 22 if self._port is None else self._port
    
    def __str__(self):
        return '%(scheme)s://%(username)s:%(password)s@%(hostname)s:%(path)s' % vars(self)

def ssh_parse_url(url):
    return SSHUrl(url)


def ssh_listdir(server, directory, keyfile=None, username=None, password=None, verbose=False):
    import pickle
    
    python_script = '''import os, os.path, sys, pickle
directory = sys.argv[-1]
if os.path.isdir(directory):
    items = {}
    for d in os.listdir(directory):
        fullpath = os.path.join(directory, d)
        d_s = os.stat(fullpath)
        items[d] = d_s
else:
    items = None
os.write(sys.stdout.fileno(), pickle.dumps(items))'''

    args = ['/usr/bin/python3'] if python_is_version3 else ['/usr/bin/python']
    args.append('-c')
    args.append(python_script)
    args.append(directory)

    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, args, keyfile=keyfile, username=username, password=password, verbose=verbose)
    if sts == 0:
        ret = pickle.loads(stdoutdata)
    else:
        ret = None
    return ret

def ssh_mkdir(server, directory, recursive=False, keyfile=None, username=None, password=None, verbose=False):
    args = ['mkdir']
    if recursive:
        args.append('-p')
    args.append(directory)
    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, args, keyfile=keyfile, username=username, password=password, verbose=verbose)
    return True if sts == 0 else False

def ssh_rmdir(server, directory, recursive=False, keyfile=None, username=None, password=None, verbose=False):
    args = ['rm', '-f']
    if recursive:
        args.append('-r')
    args.append(directory)
    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, args, keyfile=keyfile, username=username, password=password, verbose=verbose)
    return True if sts == 0 else False

class ConnectionTempFile(object):
    def __init__(self, cxn, name):
        self._cxn = cxn
        self.name = name

    def __del__(self):
        self.close()

    def close(self):
        return self._cxn.delete_temp_file(self)

class SSHConnection(object):
    def __init__(self, url=None, hostname=None, port=None, username=None, password=None, keyfile=None, verbose=False):
        if url is None:
            self.hostname = hostname
            self.port = port
            self.username = username
            self.password = password
        else:
            self.username = url.username
            self.port = url.port
            self.password = url.password
            self.hostname = url.hostname
        self.keyfile = keyfile
        self.sudo_session = None
        self.verbose = verbose
        self._temp_files = []

    def __del__(self):
        for tmp in self._temp_files:
            tmp.close()
        self.close()

    def __str__(self):
        return '%s(%s@%s:%i)' % (self.__class__.__name__, self.username, self.hostname, self.port)

    def close(self):
        if self.sudo_session:
            self.sudo_session.close()
        if self.keyfile:
            self.keyfile.close()

    def create_temp_file(self, data, mode=0o600):
        ret = None
        tmpfile = ssh_create_temp_file(self.hostname, data,
                                        sudo_command=None, sudo_env=None,
                                        keyfile=self.keyfile, username=self.username, verbose=self.verbose)
        if tmpfile:
            ret = ConnectionTempFile(self, tmpfile)
            self._temp_files.append(ret)
        return ret

    def delete_temp_file(self, tmpfile):
        ret = True
        if tmpfile.name is not None:
            cleanup_args = ['/bin/rm', '-f', tmpfile.name]
            (cleanup_sts, cleanup_stdout, cleanup_stderr) = ssh_runcmdAndGetData(self.hostname, cleanup_args,
                                                                                sudo_command=None, sudo_env=None,
                                                                                keyfile=self.keyfile, username=self.username, verbose=self.verbose)
            if cleanup_sts == 0:
                tmpfile.name = None
        return ret

    def to_commandline(self, args, env=None, sudo=False):
        if self.sudo_session and sudo:
            return self.sudo_session.to_commandline(args, env)
        else:
            return to_commandline([args] if isinstance(args, str) else args, env=env)

    def runcmdAndGetData(self, args=None, script=None,
                useTerminal=False, sudo=False,
                outputStdErr=False, outputStdOut=False,
                stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None,
                allocateTerminal=False, x11Forwarding=False, cwd=None, env=None,
                quote_char='\''):

        if useTerminal:
            used_stdin = sys.stdin if stdin is None else stdin
            used_stdout = sys.stdout if stdout is None else stdout
            used_stderr = sys.stderr if stderr is None else stderr
        else:
            used_stdin = None
            used_stdout = None
            used_stderr = None
        sudo_command = None
        sudo_env = None
        if sudo:
            if self.sudo_session:
                sudo_command = self.sudo_session.command_prefix
                sudo_env = self.sudo_session.environment
            else:
                # No sudo session available, so failure immediately
                raise SudoSessionException(self, 'No sudo session available')

        return ssh_runcmdAndGetData(self.hostname, args=args, script=script,
                                                     outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                                     stdin=used_stdin, stdout=used_stdout, stderr=used_stderr,
                                                     stderr_to_stdout=stderr_to_stdout,
                                                     cwd=cwd, env=env,
                                                     sudo_command=sudo_command, sudo_env=sudo_env,
                                                     allocateTerminal=allocateTerminal, x11Forwarding=x11Forwarding,
                                                     quote_char=quote_char,
                                                     keyfile=self.keyfile, username=self.username, verbose=self.verbose)

    def copy_id(self, public_keyfile,
                outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                ssh_copy_id_executable=SSH_COPY_ID_EXECUTABLE, use_putty=SSH_COPY_ID_USE_PUTTY):

        return ssh_copy_id(public_keyfile=public_keyfile, server=self.hostname, username=self.username,
                     verbose=self.verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                     stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env,
                     ssh_copy_id_executable=ssh_copy_id_executable, use_putty=use_putty)

class SudoSessionBase(object):
    def __init__(self, cxn, sudo_password=None):
        self._cxn = cxn
        self.sudo_password = sudo_password
        self.sudo_askpass_script = None
        self.sudo_command = None
        self.sudo_user_id = None
        self.sudo_env = {}

    @property
    def verbose(self):
        return self._cxn.verbose

    @property
    def user_id(self):
        return self.sudo_user_id

    @property
    def command_prefix(self):
        return self.sudo_command

    @property
    def environment(self):
        return self.sudo_env

    def to_commandline(self, args, env=None, sudo=False):
        sudo_env_str = ''
        for (env_key, env_value) in self.sudo_env.items():
            if sudo_env_str:
                sudo_env_str += ' '
            sudo_env_str += '%s=\'%s\'' % (env_key, env_value)

        commandline = to_commandline([args] if isinstance(args, str) else args, env=env)
        return '%s %s %s' % (sudo_env_str, self.sudo_command, commandline)

class SudoSessionException(Exception):
    def __init__(self, cxn, msg):
        self.cxn = cxn
        self.msg = msg

    def __str__(self):
        return 'SudoSessionException %s: %s' % (str(self.cxn), str(self.msg))


class SSHSudoSession(SudoSessionBase):
    def __init__(self, cxn, sudo_password=None):
        SudoSessionBase.__init__(self, cxn, sudo_password)
        if self._cxn is not None:
            self.start()

    def __del__(self):
        self.close()

    def start(self):
        self.close()
        script = """
tmpfile=`mktemp`
echo "#!/bin/sh\necho \"%(sudo_password)s\"\n" > "$tmpfile"
chmod 700 "$tmpfile"
SUDO_ASKPASS="$tmpfile" sudo -A /bin/true; RES=$?
if [ $RES -eq 0 ]; then
    echo "$tmpfile"
else
    rm -f "$tmpfile"
fi
exit $RES
""" % { 'sudo_password': self.sudo_password }
        (sts, stdout, stderr) = self._cxn.runcmdAndGetData(script=script)
        ret = True if sts == 0 else False
        if ret:
            #print (sts, stdout, stderr)
            self.sudo_askpass_script = stdout.strip().decode()
            self.sudo_env['SUDO_ASKPASS'] = self.sudo_askpass_script
            self.sudo_command = 'sudo -A'
            self._cxn.sudo_session = self
        return ret

    def close(self):
        if self.sudo_askpass_script:
            (sts, stdout, stderr) = self._cxn.runcmdAndGetData(args=['rm', '-f', self.sudo_askpass_script])
            ret = True if sts == 0 else False
            self.sudo_askpass_script = None
            self.sudo_command = None
        else:
            ret = True
        return ret

class SSHSessionKey(object):
    def __init__(self, cxn, name=None):
        self._temp_directory = None
        if name is None:
            self._public_key_comment = '%s@%s' % (self.__class__.__name__, gethostname(fqdn=True))
        else:
            self._public_key_comment = name
        self._private_keyfile = None
        self._public_keyfile = None
        self._cxn = cxn
        if self._cxn is not None:
            self.start()

    def __del__(self):
        self.close()

    @property
    def verbose(self):
        return self._cxn.verbose

    @property
    def keyfile(self):
        return self._private_keyfile

    def close(self):
        if self._public_keyfile:
            if self._cxn.verbose:
                print('remove key %s' % self._public_key_comment)
            args = ['sed', '/%s/d' % self._public_key_comment, '-i.old', '$HOME/.ssh/authorized_keys']
            (sts, stdout, stderr) = self._cxn.runcmdAndGetData(args=args, quote_char='"')
            ret = True if sts == 0 else False
            self._public_keyfile = None
        else:
            ret = True
        if self._temp_directory is not None:
            for f in os.listdir(self._temp_directory):
                full = os.path.join(self._temp_directory, f)
                os.remove(full)
            os.rmdir(self._temp_directory)
            self._temp_directory = None
        return ret

    def start(self):
        self.close()
        ret = False
        if self._private_keyfile is None:
            self._temp_directory = tempfile.mkdtemp()
            keyfile = os.path.join(self._temp_directory, self.__class__.__name__)

            (private_keyfile, public_keyfile) = ssh_keygen(keyfile, comment=self._public_key_comment, verbose=self._cxn.verbose)
            if private_keyfile and public_keyfile:
                if self._cxn.copy_id(public_keyfile):
                    self._private_keyfile = private_keyfile
                    self._public_keyfile = public_keyfile
                    if self._cxn.keyfile is None:
                        self._cxn.keyfile = self
                    ret = True
                elif self.verbose:
                    print('Failed to copy SSH key %s to %s' % (public_keyfile, str(self._cxn)))
            elif self.verbose:
                print('Failed to generate SSH key')
            if not ret:
                for f in os.listdir(self._temp_directory):
                    full = os.path.join(self._temp_directory, f)
                    os.remove(full)
                os.rmdir(self._temp_directory)
                self._temp_directory = None
        else:
            ret = True
        return ret

class LocalConnection(object):
    def __init__(self, verbose=False):
        self.hostname = 'localhost'
        self.port = 0
        self.username = None
        self.password = ''
        self.keyfile = None
        self.sudo_session = None
        self.verbose = verbose
        self._temp_files = []

    def __del__(self):
        self.close()

    def __str__(self):
        return '%s(%s@%s:%i)' % (self.__class__.__name__, self.username, self.hostname, self.port)

    def close(self):
        for tmp in self._temp_files:
            tmp.close()
        self.sudo_session = None

    def create_temp_file(self, data, mode=0o600):
        ret = None
        try:
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            tmpfile.write(data.encode())
            ret = ConnectionTempFile(self, tmpfile.name)
            tmpfile.close()
            os.chmod(tmpfile.name, mode)
            self._temp_files.append(ret)
        except IOError:
            pass
        return ret

    def delete_temp_file(self, tmpfile):
        ret = True
        if tmpfile.name is not None:
            if os.path.isfile(tmpfile.name):
                os.unlink(tmpfile.name)
            tmpfile.name = None
        return ret

    def to_commandline(self, args, env=None, sudo=False):
        if self.sudo_session and sudo:
            return self.sudo_session.to_commandline(args, env)
        else:
            return to_commandline([args] if isinstance(args, str) else args, env=env)

    def runcmdAndGetData(self, args=[], script=None,
                useTerminal=False, sudo=False,
                outputStdErr=False, outputStdOut=False,
                stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None,
                allocateTerminal=False, x11Forwarding=False, cwd=None, env=None,
                quote_char='\''):

        if useTerminal:
            used_stdin = sys.stdin if stdin is None else stdin
            used_stdout = sys.stdout if stdout is None else stdout
            used_stderr = sys.stderr if stderr is None else stderr
        else:
            used_stdin = None
            used_stdout = None
            used_stderr = None

        if not sudo or isRoot():
            return runcmdAndGetData(args, script=script, verbose=self.verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                    stdin=used_stdin, stdout=used_stdout, stderr=used_stderr, stderr_to_stdout=stderr_to_stdout,
                                    input=input, cwd=cwd, env=env)
        elif self.sudo_session is None:
            # No sudo session available, so failure immediately
            raise SudoSessionException(self, 'No sudo session available')
        else:
            real_args = ['/usr/bin/sudo', '-A']
            real_args.extend(args)
            real_env = env if env else os.environ
            for (k, v) in self.sudo_session.environment.items():
                real_env[k] = v

            return runcmdAndGetData(real_args, script=script, verbose=self.verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                    stdin=used_stdin, stdout=used_stdout, stderr=used_stderr, stderr_to_stdout=stderr_to_stdout, input=input, cwd=cwd, env=real_env)

class LocalSudoSession(SudoSessionBase):
    def __init__(self, cxn, sudo_password=None):
        SudoSessionBase.__init__(self, cxn, sudo_password)
        if self._cxn is not None:
            self.start()

    def __del__(self):
        self.close()

    def start(self):
        self.close()
        ret = True
        try:
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            s = "#!/bin/sh\necho \"%s\"\n" % self.sudo_password
            tmpfile.write(s.encode())
            self.sudo_askpass_script = tmpfile.name
            tmpfile.close()
            os.chmod(self.sudo_askpass_script, 0o700)
            self.sudo_env['SUDO_ASKPASS'] = self.sudo_askpass_script
            self.sudo_command = 'sudo -A'
            self._cxn.sudo_session = self
        except IOError:
            ret = False
            pass
        return ret

    def close(self):
        if self.sudo_askpass_script:
            try:
                os.remove(self.sudo_askpass_script)
            except OSError:
                pass
        self.sudo_command = None
        return True

class ScreenSession(object):

    DEFAULT_CONFIG = {
        'startup_message': 'off',
        'deflogin': 'on',
        'vbell': 'off',
        'vbell_msg': '\'Bell!\'',
        'defscrollback': 100000,
        'defnonblock': 5,
        'bind': ['^k','^\\', '\\\\ quit', 'K kill', 'I login on', 'O login off', '} history'],
        'hardstatus': 'alwayslastline',
        'hardstatus string': '\'%{= kG}[ %{G}%H %{g}][%= %{=kw}%?%-Lw%?%{r}(%{W}%n*%f%t%?(%u)%?%{r})%{w}%?%+Lw%?%?%= %{g}][%{B}%Y-%m-%d %{W}%c %{g}]\'',
        'termcapinfo': [
            'vt100 dl=5\\E[M',
            'xterm*|rxvt*|kterm*|Eterm* hs:ts=\\E]0;:fs=\\007:ds=\\E]0;\\007',
            'xterm*|linux*|rxvt*|Eterm* OP',
            'xterm \'is=\\E[r\\E[m\\E[2J\\E[H\\E[?7h\\E[?1;4;6l\'',
            'xterm|xterms|xs|rxvt ti@:te@'
            ],
        }

    def __init__(self, cxn, name=None, sudo=None, config=None):
        self._cxn = cxn
        self._sudo = sudo
        if name is None:
            self._name = '%s@%s' % (self.__class__.__name__, gethostname(fqdn=True))
        else:
            self._name = name
        self._config = config if config else self.DEFAULT_CONFIG
        self._config_file = None
        if self._cxn is not None:
            self.start()

    def __del__(self):
        self.close()
        if self._config_file is not None:
            self._config_file.close()

    @property
    def verbose(self):
        return self._cxn.verbose

    @property
    def connection(self):
        return self._cxn

    def start(self, detached=True):
        args=['screen', '-S', self._name]
        if detached:
            args.append('-d')
            args.append('-m')
        if self._config:
            config_data = ''
            if isinstance(self._config, dict):
                for k,v in self._config.items():
                    if isinstance(v, list):
                        for li in v:
                            config_data += '%s %s\n' % (k,li)
                    else:
                        config_data += '%s %s\n' % (k,v)
            self._config_file = self._cxn.create_temp_file(config_data)

        if self._config_file:
            args.append('-c')
            args.append(self._config_file.name)
        (sts, stdout, stderr) = self._cxn.runcmdAndGetData(args=args, allocateTerminal=True)
        ret = True if sts == 0 else False
        return ret

    def _send_command(self, args, window_number=-1):
        real_args=['screen']
        if self._config_file:
            real_args.append('-c')
            real_args.append(self._config_file.name)
        real_args.append('-S')
        real_args.append(self._name)
        if window_number != -1:
            real_args.append('-p')
            real_args.append('%i' % window_number)
        real_args.append('-X')
        real_args.extend(args)
        (sts, stdout, stderr) = self._cxn.runcmdAndGetData(args=real_args)
        ret = True if sts == 0 else False
        return ret

    def quit(self):
        return self._send_command(['quit'])

    def close(self):
        return self.quit()

    def logfile(self, filename, window_number=-1):
        return self._send_command(['logfile', filename], window_number)

    def log(self, value, window_number=-1):
        return self._send_command(['log', 'on' if value else 'off'], window_number)

    def echo(self, message, window_number=-1):
        return self._send_command(['echo', message], window_number)

    def stuff(self, data, window_number=0):
        return self._send_command(['stuff', data], window_number)

    def runcmdAndGetData(self, args=[], script=None,
                useTerminal=False, sudo=False, shell='/bin/sh',
                outputStdErr=False, outputStdOut=False,
                stdin=None, stdout=None, stderr=None, stderr_to_stdout=False, input=None, cwd=None, env=None,
                allocateTerminal=False, x11Forwarding=False,
                quote_char='\'', window_number=-1):

        real_args=['screen']
        if self._config_file:
            real_args.append('-c')
            real_args.append(self._config_file.name)
        real_args.append('-S')
        real_args.append(self._name)
        if window_number != -1:
            real_args.append('-p')
            real_args.append('%i' % window_number)

        script_file = None
        if script is None:
            real_args.extend(args)
        else:
            script_file = self._cxn.create_temp_file(script)
            real_args.append(shell)
            real_args.append(script_file.name)

        (sts, stdout, stderr) = self._cxn.runcmdAndGetData(args=real_args, sudo=sudo,
                                                           outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                                            stdin=stdin, stdout=stdout, stderr=stderr, stderr_to_stdout=stderr_to_stdout,
                                                            useTerminal=useTerminal, allocateTerminal=allocateTerminal, x11Forwarding=x11Forwarding,
                                                            input=input, cwd=cwd, env=env, quote_char=quote_char)
        if script_file:
            script_file.close()

        return (sts, stdout, stderr)
