#!/usr/bin/env python

import os
import sys
import re
import json
import cli

from cli import simpath

Version = (0, 9)
Prefix_Str = '''
########################################################################
#
# Automatically generated by crmake %d.%d
#
########################################################################
''' % Version

HList = []
CList = []
CXXList = []

Targets = {}

Makefiles = {}

Exclude = []

Protect = ['proto', 'hList', 'cxxList', 'cList', 'apply_state']

class Makefile:
    def __init__(self, setting={}):
        self.proto = {}
        self.apply_state = 0
        self.type = 'pro'

        self.name = 'main' #the name of this object, e.g foo
        self.target = '' #target'filename needn't be the same with name
        self.makefile = 'Makefile' #pathname of Makefile

        self.srcdir = '.' #the directory or file including the target's source
        self.tgtdir = 'bin' #path for the target
        self.objdir = 'obj' #path for intermedia files like *.o

        self.hList = set()
        self.cxxList = set()
        self.cList = set()

        self.includePath = set() #-I
        self.libPath = set() #-L
        self.libName = set() #-l
        self.modules = '' #pkg-config

        self.CC = 'gcc'
        self.CXX = 'g++'
        self.LD = 'g++'
        self.AR = 'ar'
        self.RM = 'rm -v'
        self.RMDIR = 'rmdir -v'
        self.INSTALL = 'install'
        self.SYMLINK = 'ln -sv'
        self.MKDIRS = 'mkdir -p'
        self.CFLAGS = '-fPIC -Wall'
        self.CXXFLAGS = '-fPIC -Wall'
        self.SHAREDFLAGS = '-shared'
        self.LDFLAGS = '-fPIC -Wall'
        self.DBGFLAGS = '-g'
        self.OPTFLAGS = '-O2'
        self.DEST = '/'
        self.PREFIX = '/usr'
        self.BINDIR = '/bin'
        self.LIBDIR = '/lib'

        self.subtgt = set() #list of names of Makefiles this target depends on
        self.tar = True
        self.opendir = True
        self.debug = True
        self.install = True

        if setting != {}:
            self.add_conf(setting)

    def add_conf(self, setting):
        if type(setting) != dict:
            return
        if 'inh' in setting and type(setting['inh']) == str:
            self.inh = setting['inh']
        for key in setting:
            if hasattr(self, key) and not (key in Protect) and \
                    type(getattr(self, key)) == type(setting[key]):
                self.proto[key] = setting[key]
        self.apply_state = 0

    def check_add(self):
        self.setdefault('srcdir', '.')
        self.setdefault('name', os.path.basename(os.path.abspath(self.srcdir)))
        self.setdefault('target', self.name)
        self.setdefault('makefile', 'Makefile')
        self.setdefault('tgtdir', 'bin')
        self.setdefault('objdir', 'obj')

        self.setdefault('CC', 'gcc')
        self.setdefault('CXX', 'g++')
        self.setdefault('LD', 'g++')
        self.setdefault('AR', 'ar')
        self.setdefault('RM', 'rm -v')
        self.setdefault('MKDIRS', 'mkdir -p')
        self.setdefault('INSTALL', 'install')
        self.setdefault('SYMLINK', 'ln -s')

        self.setdefault('DEST', '/')
        self.setdefault('PREFIX', '/usr')
        self.setdefault('BINDIR', '/bin')
        self.setdefault('LIBDIR', '/lib')
        self.makefile = simpath(self.makefile)

    def setdefault(self, attr, default):
        if hasattr(self, attr) \
                and getattr(self, attr) != set() and getattr(self, attr) != '':
            return
        setattr(self, attr, default)

    def apply_conf(self):
        if self.apply_state:
            return
        self.apply_state = -1
        if hasattr(self, 'inh'):
            if self.inh in Makefiles:
                if Makefiles[self.inh].state == -1:
                    os.exit(-1)
                Makefiles[self.inh].apply_conf()
                inh = Makefiles[self.inh].proto
                for key in inh:
                    if not key in self.proto:
                        self.proto[key] = inh[key]
        for key in self.proto:
            setattr(self, key, self.proto[key])
        self.apply_state = 1

    def write(self):
        self.targets = set()
        self.ndirs = set()
        pid = os.fork()
        if pid == -1:
            exit(-1)
        if pid:
            os.waitpid(pid, 0)
            return
        f = open(self.makefile, 'w')
        os.chdir(os.path.dirname(self.makefile))
        f.write(Prefix_Str + '\n')
        f.flush()
        if self.type == 'pro':
            self.write_pro(f)
        self.write_ndirs(f)
        self.write_clean(f)
        f.close()
        exit(0)

    def write_clean(self, f):
        f.write('.PHONY: clean cleandir\n')
        f.write('clean:\n')
        f.write('\t@echo cleaning...\n')
        f.write('\t@$(RM)')
        for target in self.targets:
            f.write(' ' + target)
        f.write(' 2> /dev/null || true\n')
        f.write('\t@make cleandir\n')
        f.write('cleandir:\n')
        f.write('\t@echo cleaning dirs...\n')
        f.write('\t@find -depth -type d -a ! -name ".*" -a ! -regex ".*/\\..*" -a -exec $(RMDIR) {} \\; 2> /dev/null || true\n')
        f.flush()

    def write_vars(self, f):
        for key in ['CC', 'CXX', 'LD', 'AR', 'RM', 'RMDIR', 'SHAREDFLAGS', 'MKDIRS', 'INSTALL', 'SYMLINK', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS', 'DBGFLAGS', 'OPTFLAGS', 'DEST', 'PREFIX', 'BINDIR', 'LIBDIR', 'name', 'target', 'srcdir', 'tgtdir', 'objdir', 'modules', 'OBJECTS', 'DBGOBJECTS']:
            if hasattr(self, key):
                f.write(key + ' = ' + getattr(self, key) + '\n')
        f.flush()

    def write_pro(self, f):
        self.include_list()
        self.o_list()
        if self.debug:
            self.dbg_o_list()
        self.write_vars(f)
        f.write('all: $(tgtdir)/$(target)\n')
        f.write('.PHONY: all\n')
        f.flush()
        f.write('$(tgtdir)/$(target): $(OBJECTS) | $(tgtdir)\n')
        self.targets.add('$(tgtdir)/$(target)')
        f.write('ifdef modules\n')
        f.write('\t$(LD) $$(pkg-config --libs $(modules)) $(OPTFLAGS) $(LDFLAGS) $(OBJECTS) -o $@\n')
        f.write('else\n')
        f.write('\t$(LD) $(OPTFLAGS) $(LDFLAGS) $(OBJECTS) -o $@\n')
        f.write('endif\n')

        f.flush()
        self.write_os(f)
        if self.debug:
            self.write_dbg(f)

    def write_dbg(self, f):
        f.write('debug: $(tgtdir)/$(target)_debug\n')
        f.write('.PHONY: debug\n')
        f.write('$(tgtdir)/$(target)_debug: $(DBGOBJECTS) | $(tgtdir)\n')
        self.targets.add('$(tgtdir)/$(target)_debug')
        f.write('ifdef modules\n')
        f.write('\t$(LD) $$(pkg-config --libs $(modules)) $(DBGFLAGS) $(LDFLAGS) $(DBGOBJECTS) -o $@\n')
        f.write('else\n')
        f.write('\t$(LD) $(DBGFLAGS) $(LDFLAGS) $(DBGOBJECTS) -o $@\n')
        f.write('endif\n')
        
        f.flush()
        self.write_dbgos(f)
        self.write_run(f)

    def write_run(self, f):
        f.write('.PHONY: run rdbg\n')
        f.write('run: $(tgtdir)/$(target)_debug\n')
        f.write('\t$(tgtdir)/$(target)_debug\n')
        f.write('rdbg: $(tgtdir)/$(target)_debug\n')
        f.write('\tgdb $(tgtdir)/$(target)_debug\n')
        f.flush()

    def write_dbgos(self, f):
        for o in self.dbgoList:
            f.write('%s: %s\n' % (o[0], o[1]))
            if o[2] == 'CC':
                flags = 'CFLAGS'
            else:
                flags = o[2] + 'FLAGS'
            f.write('ifdef modules\n')
            f.write('\t$(%s) $$(pkg-config --cflags $(modules)) $(DBGFLAGS) $(%s) -c $< -o $@\n' % (o[2], flags))
            f.write('else\n')
            f.write('\t$(%s) $(DBGFLAGS) $(%s) -c $< -o $@\n' % (o[2], flags))
            f.write('endif\n')
        self.targets.add('$(DBGOBJECTS)')
        f.flush()

    def write_os(self, f):
        for o in self.oList:
            f.write('%s: %s\n' % (o[0], o[1]))
            if o[2] == 'CC':
                flags = 'CFLAGS'
            else:
                flags = o[2] + 'FLAGS'
            f.write('ifdef modules\n')
            f.write('\t$(%s) $$(pkg-config --cflags $(modules)) $(OPTFLAGS) $(%s) -c $< -o $@\n' % (o[2], flags))
            f.write('else\n')
            f.write('\t$(%s) $(OPTFLAGS) $(%s) -c $< -o $@\n' % (o[2], flags))
            f.write('endif\n')
        self.targets.add('$(OBJECTS)')
        f.flush()

    def write_ndirs(self, f):
        for ndir in self.ndirs | {'$(tgtdir)', '$(objdir)'}:
            f.write(ndir + ':\n')
            f.write('\t$(MKDIRS) %s\n' % ndir)
        f.flush()

    def include_list(self):
        for h in self.hList:
            self.includePath.add(os.path.dirname(h))
        for I in self.includePath:
            self.CFLAGS += ' -I' + I
            self.CXXFLAGS += ' -I' + I

    def o_list(self):
        self.OBJECTS = ''
        c2o = re.compile('\\.c$|\\.cpp$')
        drt = re.compile('\\\\\n|\n$', re.S)
        self.oList = []
        for c in self.cList:
            [ret, out, err] = cli.asystemcli('gcc -MM ' + c + ' ' + self.CFLAGS)
            if err:
                print(err)
                exit(ret)
            o = out.split(':', 1) + ['CC']
            o[0] = '$(objdir)' + '/' + c2o.sub('.o', c)
            ndir = os.path.dirname(o[0])
            self.ndirs.add(ndir)
            o[1] = drt.sub('', o[1]) + ' | ' + ndir
            self.oList.append(o)
            self.OBJECTS += ' ' + o[0]
        for cxx in self.cxxList:
            [ret, out, err] = cli.asystemcli('gcc -MM ' + c + ' ' + self.CXXFLAGS)
            if err:
                print(err)
                exit(ret)
            o = out.split(':', 1) + ['CXX']
            o[0] = '$(objdir)' + '/' + c2o.sub('.o', cxx)
            ndir = os.path.dirname(o[0])
            self.ndirs.add(ndir)
            o[1] = drt.sub('', o[1]) + ' | ' + ndir
            self.oList.append(o)
            self.OBJECTS += ' ' + o[0]

    def dbg_o_list(self):
        self.DBGOBJECTS = ''
        c2o = re.compile('\\.c$|\\.cpp$')
        drt = re.compile('\\\\\n|\n$', re.S)
        self.dbgoList = []
        for c in self.cList:
            [ret, out, err] = cli.asystemcli('gcc -MM ' + c + ' ' + self.CFLAGS)
            if err:
                print(err)
                exit(ret)
            o = out.split(':', 1) + ['CC']
            o[0] = '$(objdir)' + '/' + c2o.sub('_debug.o', c)
            ndir = os.path.dirname(o[0])
            self.ndirs.add(ndir)
            o[1] = drt.sub('', o[1]) + ' | ' + ndir
            self.dbgoList.append(o)
            self.DBGOBJECTS += ' ' + o[0]
        for cxx in self.cxxList:
            [ret, out, err] = cli.asystemcli('gcc -MM ' + c + ' ' + self.CXXFLAGS)
            if err:
                print(err)
                exit(ret)
            o = out.split(':', 1) + ['CXX']
            o[0] = '$(objdir)' + '/' + c2o.sub('_debug.o', cxx)
            ndir = os.path.dirname(o[0])
            self.ndirs.add(ndir)
            o[1] = drt.sub('', o[1]) + ' | ' + ndir
            self.dbgoList.append(o)
            self.DBGOBJECTS += ' ' + o[0]

def getrel(path, sub):
    path = simpath(path)
    sub = simpath(sub)
    if sub == path:
        return ''
    if path[-1] != '/':
        path += '/'
    if sub.find(path) != 0:
        return
    rel = sub[len(path):len(sub)]
    if rel[0] == '/':
        rel = rel[1:len(sub)]
    return rel


def rd_config():
    try:
        conf_txt = open('crmake.in').read()
    except IOError:
        return
    conf = eval(conf_txt)
    if 'name' in conf:
        conf.pop('name')
    if 'targets' in conf and type(conf['targets']) == list:
        for target in conf['targets']:
            if target['name'] == 'main':
                continue
            Targets[target['name']] = target
        conf.pop('targets')
    return conf

def lssrc(path):
    flist = cli.find(path)
    for f in flist:
        if re.compile('[^\./]\.c$').findall(f) != []:
            CList.append(f)
        elif re.compile('[^\./]\.cpp$').findall(f) != []:
            CXXList.append(f)
        elif re.compile('[^\./]\.h$').findall(f) != []:
            HList.append(f)

def dist_files(List, field):
    for src in List:
        parent = Makefiles['main']
        for name in Makefiles:
            make = Makefiles[name]
            rel = getrel(make.srcdir, src)
            if rel == None or \
                    getrel(make.srcdir, parent.srcdir) != None:
                continue
            parent = make
        getattr(parent, field).add(src)

def dist_list():
    dist_files(CList, 'cList')
    dist_files(CXXList, 'cxxList')
    dist_files(HList, 'hList')

def main():
    conf_f = rd_config()
    mt = Makefile()
    mt.add_conf(conf_f)
    mt.apply_conf()
    mt.check_add()
    lssrc(mt.srcdir)
    Makefiles['main'] = mt
    for target in Targets:
        Makefiles[target] = Makefile(setting=Targets[target])
        Makefiles[target].apply_conf()
        Makefiles[target].check_add()
    dist_list()
    mt.write()

if __name__ == '__main__':
    main();

