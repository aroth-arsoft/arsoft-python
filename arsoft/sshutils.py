#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from utils import runcmdAndGetData, platform_is_windows, which

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
        args = ['-a', '-x', '-o', 'BatchMode=yes']
        if username:
            args.extend(['-l', username ])
        if keyfile:
            args.extend(['-i', keyfile])

    args.append(server)
    if commandline:
        args.append(commandline)
        input = None
    elif script:
        args.append('/bin/bash -')
        # convert any M$-newlines into the real-ones
        input = script.replace('\r\n', '\n')
        if verbose:
            print('script=%s' %input)
    else:
        raise ValueError('neither commandline nor script specified.')
    return runcmdAndGetData(ssh_executable, args, input=input, 
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)

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
