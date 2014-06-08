#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

import os
import sys
import socket
from utils import runcmdAndGetData

def create_unix_socket(path, mode, socktype=socket.SOCK_STREAM):
    # Make sure the socket does not already exist
    try:
        os.unlink(path)
    except OSError:
        if os.path.exists(path):
            raise

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socktype)

    # Bind the socket to the port
    sock.bind(path)

    # change permissions of the socket
    os.fchmod(sock.fileno(), mode)

    # Listen for incoming connections
    sock.listen(5)
    return sock

def close_unix_socket(sock):
    path = None
    try:
        path = sock.getsockname()
        sock.close()
    except socket.error as e:
        pass

    if path:
        # Make sure the socket does not already exist
        try:
            os.unlink(path)
        except OSError:
            if os.path.exists(path):
                raise

def connect_unix_socket(path, socktype=socket.SOCK_STREAM):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socktype)

    # Connect the socket to the port where the server is listening
    sock.connect(path)
    return sock

def send_unix_socket_message(path, message, socktype=socket.SOCK_STREAM):
    try:
        sock = connect_unix_socket(path, socktype)
    except socket.error as e:
        sock = None
    ret = -1
    if sock is not None:
        try:
            sock.sendall(message)
            ret = len(message)
        finally:
            sock.close()
    return ret

def sethostname(new_hostname):
    (sts, stdoutdata, stderrdata) = runcmdAndGetData('/bin/hostname', [new_hostname])
    ret = True if sts == 0 else False
    return ret
