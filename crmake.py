#!/usr/bin/env python

import os
import sys

Opts = {
    'tar' : True,
    'opendir' : True,
    'debug' : True,
    }

Vars = {
    'Name' : '',
    'hList' : [],
    'cppList' : [],
    'cList' : [],
    'includePath' : [],
    'libPath' : [],
    'libName' : [],
    'CFLAGS' : [],
    'CPPFLAGS' : [],
    'LDFLAGS' : [],
    'MAKEFILE' : 'Makefile',
    'root' : '/',
    'PREFIX' : '/usr',
    'bindir' : '/bin',
    'libdir' : '/lib',
    'dataroot' : '/share'
    }

def find(path):
    children = os.listdir(path)
    res = []
    for child in children:
        full = path + '/' + child
        res.append(full)
        if os.path.isdir(full) & (not os.path.islink(full)):
            res += find(full)
    return res

def main():
    i = 0
    while (i < len(sys.argv)):
        if sys.argv[i] == '-I':
            i += 1;
            Vars['includePath'].append(sys.argv[i])
        elif sys.argv[i] == '-L':
            i += 1;
            Vars['libPath'].append(sys.argv[i])
        elif sys.argv[i] == '-l':
            i += 1;
            Vars['libName'].append(sys.argv[i])
        elif '+=' in sys.argv[i]:
            [key, value] = sys.argv[i].split('=', 1)
            if key in Vars:
                Vars[key].append(value)
        elif sys.argv[i] == '-o':
            i += 1
            Vars['MAKEFILE'] = sys.argv[i]
        elif '=' in sys.argv[i]:
            [key, value] = sys.argv[i].split('=', 1)
            Vars[key] = value
        elif sys.argv[i] == '--notar':
            Opts['tar'] = False
        elif sys.argv[i] == '--noopen':
            Opts['opendir'] = False
        elif sys.argv[i] == '--nodebug':
            Opts['tar'] = False
        i += 1


if __name__ == '__main__':
    main();
