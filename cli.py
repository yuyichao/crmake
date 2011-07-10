#!/usr/bin/env python

import os
import re

from os.path import basename, dirname

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

def simpath(path):
    path = os.path.normpath(path)
    if path.startswith('//'):
        path = path[1:]
    return path

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

def delcommon(lst1, lst2):
    i = 0
    while i < min(len(lst1), len(lst2)):
        if lst1[i] != lst2[i]:
            break
        i += 1
    return [lst1[i:], lst2[i:]]

def splitpath(path):
    if path == '':
        path = '.'
    ret = path.split('/')
    while len(ret) > 1 and ret[0] == '' and ret[1] == '':
        ret.pop(0)
    return ret

def getrel(path1, path2):
    path1 = splitpath(simpath(path1))
    path2 = splitpath(simpath(path2))
    if (path1[0] and not path2[0]) or (path2[0] and not path1[0]):
        return [None, None]
    [path1, path2] = delcommon(path1, path2)
    if path2 and (path2[0] in ['..']):
        rel1 = None
    else:
        rel1 = simpath('/'.join(['..'] * (len(path2) - path2.count('.'))
                                + path1))
    if path1 and (path1[0] in ['..']):
        rel2 = None
    else:
        rel2 = simpath('/'.join(['..'] * (len(path1) - path1.count('.'))
                                + path2))
    return [rel1, rel2]

