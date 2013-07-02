#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from utils import runcmdAndGetData, platform_is_windows, which

def _find_ssh_executable(ssh=None, scp=None):
    if ssh:
        if os.access(ssh, os.X_OK):
            exec_path = os.path.abspath(ssh)
            exec_basename = os.path.base(exec_path).lower()
            if exec_basename == 'putty' or exec_basename == 'putty.exe':
                exec_putty = True
            else:
                exec_putty = False
        else:
            exec_path = None
            exec_putty = False
    else:
        if platform_is_windows:
            candidates = which('putty.exe')
            exec_path = candidates[0] if len(candidates) > 0 else None
            exec_putty = True
        else:
            candidates = which('ssh')
            exec_path = candidates[0] if len(candidates) > 0 else None
            exec_putty = False
    return (exec_path, exec_putty)

def _find_scp_executable(scp=None):
    if scp:
        if os.access(scp, os.X_OK):
            exec_path = os.path.abspath(scp)
            exec_basename = os.path.base(exec_path).lower()
            if exec_basename == 'plink' or exec_basename == 'plink.exe':
                exec_putty = True
            else:
                exec_putty = False
        else:
            exec_path = None
            exec_putty = False
    else:
        if platform_is_windows:
            candidates = which('plink.exe')
            exec_path = candidates[0] if len(candidates) > 0 else None
            exec_putty = True
        else:
            candidates = which('scp')
            exec_path = candidates[0] if len(candidates) > 0 else None
            exec_putty = False
    return (exec_path, exec_putty)

(SSH_EXECUTABLE, SSH_USE_PUTTY) = _find_ssh_executable()
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
        args = ['-a', '-x']
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
    else:
        raise ValueError('neither commandline nor script specified.')
    return runcmdAndGetData(ssh_executable, args, input=input, 
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)

def scp(server, files, target_dir, keyfile=None, username=None, password=None, 
                         verbose=False, outputStdErr=False, outputStdOut=False, stdin=None, stdout=None, stderr=None, cwd=None, env=None,
                         sch_executable=SCP_EXECUTABLE, use_putty=SCP_USE_PUTTY):

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

    return runcmdAndGetData(sch_executable, args, input=None, 
                            verbose=verbose, outputStdErr=outputStdErr, outputStdOut=outputStdOut, 
                            stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd, env=env)
 
