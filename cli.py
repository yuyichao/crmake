#!/usr/bin/env python

import os
import re

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

    out = readall(fdout[0], decode=decode)
    err = readall(fderr[0], decode=decode)
    os.close(fdout[0])
    os.close(fderr[0])
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

    out = readall(fdout[0], decode=decode)
    err = readall(fderr[0], decode=decode)
    os.close(fdout[0])
    os.close(fderr[0])
    return [ret, out, err]


def readall(fd, decode=True):
    res = bytes()
    while True:
        buf = os.read(fd, 65536)
        if len(buf) == 0:
            break
        res += buf
    res = res.decode('UTF-8')
    return res


def find(path):
    try:
        children = os.listdir(path)
    except OSError:
        return []
    res = []
    for child in children:
        full = path + '/' + child
        res.append(full)
        if os.path.isdir(full) & (not os.path.islink(full)):
            res += find(full)
    return res

def mimeof(path):
    ret = asystem(['xdg-mime', 'query', 'filetype', path])
    if ret[0]:
        return ''
    return ret[1]

def simpath(path):
    while True:
        tmp = simpath1(path)
        if tmp == path:
            return tmp
        path = tmp

def simpath1(path):
    path = re.sub('(/(?!(\\.|)\\./)[^/]/\\.\\.(/|$))', '/', path)
    path = re.sub('(^(?!(\\.|)\\./)[^/]/\\.\\.(/|$))', './', path)
    path = re.sub('^\\./(?!/|$)', '', path)
    path = re.sub('/\\.(/|$)', '/', path)
    path = re.sub('^/\\.\\.(/|$)', '/', path)
    path = re.sub('/+', '/', path)
    return path
