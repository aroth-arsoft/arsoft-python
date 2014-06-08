#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from utils import runcmdAndGetData, platform_is_windows, which
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
            candidates = which(putty_name + '.exe')
            exec_path = candidates[0] if len(candidates) > 0 else None
            exec_putty = True
        else:
            candidates = which(ssh_name)
            exec_path = candidates[0] if len(candidates) > 0 else None
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

def ssh_runcmdAndGetData(server, commandline=None, script=None, keyfile=None, username=None, password=None, 
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         allocateTerminal=False, x11Forwarding=False,
                         ssh_executable=SSH_EXECUTABLE, use_putty=SSH_USE_PUTTY):

    if use_putty:
        args = ['-batch', '-noagent', '-a', '-x']
        if username:
            args.extend(['-l', username ])
        if keyfile:
            args.extend(['-i', keyfile])
        elif password:
            args.extend(['-pw', password])
    else:
        args = ['-a', '-o', 'BatchMode=yes']
        if username:
            args.extend(['-l', username ])
        if keyfile:
            args.extend(['-i', keyfile])
        args.append( '-t' if allocateTerminal else '-T')
        args.append( '-X' if x11Forwarding else '-x')

    args.append(server)
    if commandline:
        args.append(commandline)
        input = None
        return runcmdAndGetData(ssh_executable, args,
                                verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut,
                                stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)

    elif script:
        tmpfile = '/tmp/arsoft_remote_ssh_%s.sh' % uuid.uuid4()
        put_args = copy.deepcopy(args)
        put_args.append('/bin/cat > ' + tmpfile)
        cleanup_args = copy.deepcopy(args)
        cleanup_args.append('/bin/rm -f ' + tmpfile)
        exec_args = copy.deepcopy(args)
        exec_args.append('/bin/bash ' + tmpfile)

        # convert any M$-newlines into the real-ones
        real_script = script.replace('\r\n', '\n')

        (put_sts, put_stdout, put_stderr) = runcmdAndGetData(ssh_executable, put_args, input=real_script,
                                verbose=verbose)

        if put_sts == 0:
            if verbose:
                print(real_script)
            (sts, stdout_data, stderr_data) = runcmdAndGetData(ssh_executable, exec_args,
                                verbose=verbose, outputStdErr=outputStdErr, outputStdOut=True,
                                stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
        else:
            (sts, stdout_data, stderr_data) = (put_sts, put_stdout, put_stderr)

        (cleanup_sts, cleanup_stdout, cleanup_stderr) = runcmdAndGetData(ssh_executable, cleanup_args,
                                verbose=verbose)
        return (sts, stdout_data, stderr_data)
    else:
        raise ValueError('neither commandline nor script specified.')

def scp(server, files, target_dir, keyfile=None, username=None, password=None, 
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         scp_executable=SCP_EXECUTABLE, use_putty=SCP_USE_PUTTY):

    if use_putty:
        args = ['-batch', '-noagent', '-q', '-l']
        if username:
            args.extend(['-l', username ])
        if keyfile:
            args.extend(['-i', keyfile])
        elif password:
            args.extend(['-pw', password])
    else:
        # enable batch-mode, compression and quiet (no progress)
        args = ['-B', '-C', '-q']
        if keyfile:
            args.extend(['-i', self._keyfile])

    args.extend(files)
    if use_putty or username is None:
        args.append(server + ':' + target_dir)
    else:
        args.append(username + '@' + server + ':' + target_dir)

    return runcmdAndGetData(scp_executable, args, input=None, 
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
 

def ssh_keygen(dest_filename, password=None, comment=None, keytype='rsa',
                     verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                     ssh_keygen_executable=SSH_KEYGEN_EXECUTABLE, use_putty=SSH_KEYGEN_USE_PUTTY):
    
    if use_putty:
        args = []
    else:
        args = ['-t', keytype, '-f', dest_filename]
        if password is None:
            args.extend(['-N', ''])
        else:
            args.extend(['-N', password])
        if comment:
            args.extend(['-C', comment])

    (sts, stdout, stderr) = runcmdAndGetData(ssh_keygen_executable, args, input=None, 
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
    if sts == 0:
        return (dest_filename, dest_filename + '.pub')
    else:
        return (None, None)

def ssh_copy_id(public_keyfile, server, username=None,
                     verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                     ssh_copy_id_executable=SSH_COPY_ID_EXECUTABLE, use_putty=SSH_COPY_ID_USE_PUTTY):
    if use_putty:
        args = []
    else:
        args = ['-i', public_keyfile]
        if username:
            args.append('%s@%s' % (username, server))
        else:
            args.append(server)

    (sts, stdout, stderr) = runcmdAndGetData(ssh_copy_id_executable, args, input=None, 
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
        self.path = None
        if url is not None:
            self.parse(url)

    def parse(self, url, scheme='ssh'):
        idx = url.find('://')
        if idx != -1:
            self.scheme = url[0:idx]
        else:
            self.scheme = scheme
        idx = url.find('@')
        if idx != -1:
            tmp = url[0:idx]
            idx = tmp.find(':')
            if idx != -1:
                self.username = tmp[0:idx]
                self.password = tmp[idx+1:]
            else:
                self.username = tmp
                self.password = None
            tmp = url[idx + 1:]
            idx = tmp.find(':')
            if idx != -1:
                self.hostname = tmp[0:idx]
                self.path = tmp[idx+1:]
            else:
                self.hostname = tmp
                self.path = None
        else:
            self.username = None
            self.password = None
            idx = url.find(':')
            if idx != -1:
                self.hostname = url[0:idx]
                self.path = url[idx+1:]
            else:
                self.hostname = url
                self.path = None
        return False if self.hostname is None else True
    
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
print(pickle.dumps(items))'''

    commandline = '/usr/bin/python -c \'' + python_script + '\' \'' + directory + '\''

    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, commandline, keyfile=keyfile, username=username, password=password, verbose=verbose)
    if sts == 0:
        ret = pickle.loads(stdoutdata)
    else:
        ret = None
    return ret

def ssh_mkdir(server, directory, recursive=False, keyfile=None, username=None, password=None, verbose=False):
    if recursive:
        commandline = 'mkdir -p \'%s\'' % (directory)
    else:
        commandline = 'mkdir \'%s\'' % (directory)
    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, commandline, keyfile=keyfile, username=username, password=password, verbose=verbose)
    return True if sts == 0 else False

def ssh_rmdir(server, directory, recursive=False, keyfile=None, username=None, password=None, verbose=False):
    if recursive:
        commandline = 'rm -rf \'%s\'' % (directory)
    else:
        commandline = 'rm -f \'%s\'' % (directory)
    (sts, stdoutdata, stderrdata) = ssh_runcmdAndGetData(server, commandline, keyfile=keyfile, username=username, password=password, verbose=verbose)
    return True if sts == 0 else False

