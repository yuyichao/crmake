#!/usr/bin/env python

import os

def asystem(arg, decode=True):
    fdout = os.pipe()
    fderr = os.pipe()
    pid = os.fork()
    if pid == -1:
        return

    if pid:
        os.close(fdout[1])
        os.close(fderr[1])
        (pid, ret) = os.waitpid(pid, 0)
    else:
        os.close(fdout[0])
        os.close(fderr[0])
        os.dup2(fdout[1], 1)
        os.dup2(fderr[1], 2)
        os.execvp(arg[0], arg)
        os.close(fdout[1])
        os.close(fderr[1])
        exit(-1)

    out = readall(fdout[0])
    err = readall(fderr[0])
    os.close(fdout[0])
    os.close(fderr[0])
    if decode:
        out = out.decode('UTF-8')
        err = err.decode('UTF-8')
    return [ret, out, err]

def asystemcli(cmd, decode=True):
    fdout = os.pipe()
    fderr = os.pipe()
    pid = os.fork()
    if pid == -1:
        return

    if pid:
        os.close(fdout[1])
        os.close(fderr[1])
        (pid, ret) = os.waitpid(pid, 0)
    else:
        os.close(fdout[0])
        os.close(fderr[0])
        os.dup2(fdout[1], 1)
        os.dup2(fderr[1], 2)
        os.system(cmd)
        os.close(fdout[1])
        os.close(fderr[1])
        exit(-1)

    out = readall(fdout[0])
    err = readall(fderr[0])
    os.close(fdout[0])
    os.close(fderr[0])
    if decode:
        out = out.decode('UTF-8')
        err = err.decode('UTF-8')
    return [ret, out, err]


def readall(fd):
    res = bytes()
    while True:
        buf = os.read(fd, 65536)
        if len(buf) == 0:
            break
        res += buf
    return res
