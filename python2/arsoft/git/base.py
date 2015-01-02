#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import which, runcmdAndGetData
import platform

def find_git_executable():
    git_executable_name = 'git.exe' if platform.system() == 'Windows' else 'git'
    return which(git_executable_name, only_first=True)

def retrieve_git_version():
    ret = None
    if GIT_EXECUTABLE:
        (sts, stdoutdata, stderrdata) = runcmdAndGetData([GIT_EXECUTABLE, '--version'])
        if sts == 0:
            stdoutdata = stdoutdata.decode("utf-8")
            if stdoutdata.startswith('git version'):
                ret = stdoutdata[12:].strip()
    return ret

def retrieve_git_version_number():
    major = None
    minor = None
    release = None
    info = None
    if GIT_VERSION_STR:
        elems = GIT_VERSION_STR.split('.')
        if len(elems) >= 3:
            try:
                major = int(elems[0])
                minor = int(elems[1])
                release  = int(elems[2])
            except ValueError:
                pass
        info = elems[3] if len(elems) > 3 else None
    return (major, minor, release, info)

GIT_EXECUTABLE = find_git_executable()

GIT_VERSION_STR = retrieve_git_version()
GIT_VERSION = retrieve_git_version_number()

GIT_SERVER_HOOKS = ['pre-receive', 'post-receive', 'update', 'post-update']
GIT_CLIENT_HOOKS = ['applypatch-msg', 
                    'pre-applypatch', 
                    'post-applypatch', 
                    'pre-commit', 
                    'prepare-commit-msg', 
                    'commit-msg',
                    'post-commit', 
                    'pre-rebase',
                    'post-checkout',
                    'post-merge',
                    'pre-auto-gc'
                    'post-rewrite']
GIT_HOOKS = GIT_SERVER_HOOKS + GIT_CLIENT_HOOKS

if __name__ == '__main__':
    print('GIT_EXECUTABLE=%s' % (GIT_EXECUTABLE))
    print('GIT_VERSION_STR=%s' % (GIT_VERSION_STR))
    print('GIT_VERSION=%s' % (str(GIT_VERSION)))
    print('GIT_SERVER_HOOKS=%s' % (GIT_SERVER_HOOKS))
    print('GIT_CLIENT_HOOKS=%s' % (GIT_CLIENT_HOOKS))
    print('GIT_HOOKS=%s' % (GIT_HOOKS))
