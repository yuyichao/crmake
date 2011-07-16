#!/usr/bin/env python

import re
import cli
import os

from os.path import basename, normpath
from cli import dirname, makedirs

Version = (0, 9, 1)

VStr = ("%d.%d" if len(Version) == 2 else "%d.%d.%d") % Version

VStr += ' ' * (10 - len(VStr))

Prefix_Str = '''
########################################################################
#                                                                      #
# Automatically generated by crmake %s                         #
#                                                                      #
########################################################################
''' % VStr

class makebase:
    MakeVar = {'RM': ['rm', '-fv'],
               'RMDIR': ['rmdir', '-pv'],
               'INSTALL': ['install'],
               'SYMLINK': ['ln', '-sv'],
               'MKDIRS': ['mkdir', '-pv'],
               'CP': ['cp', '-v'],
               'TAR': ['tar', '--bzip2', '-c']
           }
    CrVar = {'src': '.',
             'makefile': 'Makefile',
             'children': [],
             'type': ['base', 'makebase', ''],
             'targets': [],  #parsed by inherited classes
             'instl_targets': [], #changes to default install list generated
             'data': {} #regexs or mime strs to specify the type of data file followed by the type of the file and the install mode
             }
    InstlDir = {'DEST': '/',
                'PREFIX': '/usr/',
                'datadir': '/share/'
                }
    InVar = {}
    fullname = re.compile('.*')
    bname = re.compile('^$')
    ignore = [re.compile('/\.[^/]')]
    mimes = []

    def __init__(self):

        '''
        init general members of the class
        '''

        self.name = 'main'
        self.makevar = self.MakeVar.copy()
        self.crvar = self.CrVar.copy()
        self.invar = self.InVar.copy()
        self.instldir = self.InstlDir.copy()

        '''
        .PHONY targets listed in the beginning of the Makefile
        '''
        self.targets = [['all', []]]

        '''
        e.g. instl_target = {'foo': 'bin'} will install foo to bindir,
        'foo': ['bar', 0o777] will install foo to bardir with mode 777
       '''
        self.instl_target = {} 
        self.rtgts = {} #e.g. {'foo': {'deps': ['bar'], 'cmd': ['\tcc bar -o foo']}}

        self.flist = []
        self.avail_f = []

    def add_avail_f(self, f):
        if type(f) == str:
            f = [f]
        self.avail_f += f

    def get_f_list(self):

        '''
        write to self.flist according to filters
        '''

        for f in self.avail_f:
            for ignore in self.ignore:
                if type(ignore) == str:
                    if ignore.find('/') >= 0:
                        if basename(f) == ignore:
                            f = None
                    else:
                        if f == ignore:
                            f = None
                else:
                    if ignore.search(f):
                        f = None
            if not f:
                continue
            if (self.fullname and self.fullname.search(f)) \
                    or (self.bname and self.bname.search(basename(f))):
                self.flist.append(f)
            else:
                mtype = cli.mimeof(f)
                for mime in self.mimes:
                    if mtype == mime:
                        self.flist.append(f)
                        break
        self.classify_files()

    def add_config(self, config):
        config = config.copy()
        for grp in [self.makevar, self.crvar, self.instldir]:
            for key in grp:
                if key in config and type(grp[key]) == type(config[key]):
                    grp[key] = config[key]
                    config.pop(key)
        for key in config:
            if key[-3:] == 'dir':
                self.instldir[key] = config[key]

    def classify_files(self): pass

    def pre_vars(self): pass

    def torel(self): pass #TODO

    def get_data_f(self):
        for f in self.avail_f:
            mtype = cli.mimeof(f)
            for cond, typ in self.crvar['data'].items():
                if mtype == cond or (type(cond) != str and cond.search(f)):
                    if len(typ) == 0:
                        typ = ['data', 0o644]
                    if len(typ) == 1:
                        if type(typ[0]) == int:
                            typ = ['data', typ[0]]
                        if type(typ[0]) == str:
                            typ = [typ[0], 0o644]
                    self.instl_target[f] = typ

    def get_ndirs(self):
        self.ndirs = []
        for name in self.instldir:
            if name == 'DEST':
                self.ndirs.append('$(DEST)')
            elif name == 'PREFIX':
                self.ndirs.append('$(DEST)/$(PREFIX)')
            else:
                self.ndirs.append('$(DEST)/$(PREFIX)/$(%s)' % name)
        for name in self.rtgts:
            self.ndirs.append(dirname(name))
        self.ndirs = delrep(self.ndirs)
        while '' in self.ndirs:
            self.ndirs.remove('')
        for tgt, deps in self.rtgts.items():
            addoptdep(deps['deps'], [dirname(tgt)])

    def guess(self):
        for tgt, typ in self.instl_target.items():
            if type(typ) == list:
                if len(typ) == 1:
                    typ = typ[0]
                else:
                    continue
            if type(typ) != str:
                continue
            if typ == 'bin':
                self.instl_target[tgt] = [typ, 0o755]
            else:
                self.instl_target[tgt] = [typ, 0o644]

    def write(self):
        makedirs(dirname(self.crvar['makefile']))
        f = open(self.crvar['makefile'], 'w')
        os.chdir(dirname(self.crvar['makefile']))
        f.write(Prefix_Str)
        f.flush()
        self.write_vars(f)
        self.write_tgts(f)
        self.write_instl(f)
        self.write_clean(f)
        self.write_dirs(f)

    def write_vars(self, f):
        for key, value in self.makevar.items():
            f.write('%s = %s\n' % (key, lst2str(value)))
        for key, value in self.instldir.items():
            f.write('%s = %s\n' % (key, lst2str(value)))
        for key, value in self.invar.items():
            f.write('%s = %s\n' % (key, lst2str(value)))
        f.flush()

    def write_tgts(self, f):
        f.write('.PHONY: %s\n' % lst2str(nths(self.targets)))
        for tgt in self.targets:
            f.write('%s: %s\n' % (tgt[0], lst2str(tgt[1])))
            if len(tgt) > 2:
                f.write('%s\n' % lst2str(tgt[2]))
        for tgt, item in self.rtgts.items():
            f.write('%s: %s\n' % (tgt, lst2str(item['deps'])))
            if 'cmd' in item:
                f.write('%s\n' % lst2str(item['cmd']))
        f.flush()

    def write_instl(self, f):
        self.guess()
        f.write('.PHONY: install uninstall\n')
        f.write('install:')
        for name in self.instldir:
            if name == 'DEST' or name == 'PREFIX':
                continue
            f.write(' $(DEST)/$(PREFIX)/$(%s)' % name)
        f.write('\n')
        for tgt, typ in self.instl_target.items():
            f.write('\t$(INSTALL) -m %o -t $(DEST)/$(PREFIX)/$(%sdir) %s\n'
                    % (typ[1], typ[0], tgt))
        f.write('uninstall:\n')
        for tgt, typ in self.instl_target.items():
            f.write('\t@$(RM) $(DEST)/$(PREFIX)/$(%sdir)/%s 2> /dev/null || true\n' % (typ[0], os.path.basename(tgt)))
        f.flush()

    def write_clean(self, f):
        f.write('.PHONY: clean\n')
        f.write('clean:\n')
        f.write('\t@echo cleaning...\n')
        f.write('\t@$(RM)')
        for target in self.rtgts:
            f.write(' ' + target)
        f.write(' 2> /dev/null || true\n')
        f.write('\t@make cleandir\n')
        f.flush()
        self.write_clean_dir(f)

    def write_clean_dir(self, f):
        f.write('.PHONY: cleandir\n')
        f.write('cleandir:\n')
        f.write('\t@echo cleaning dirs...\n')
        f.write('\t@find -depth -type d -a ! -name ".*" -a ! -regex ".*/\\..*" -a -exec $(RMDIR) {} \\; 2> /dev/null || true\n')
        f.flush()

    def write_dirs(self, f):
        for path in self.ndirs:
            f.write('%s:\n' % path)
            f.write('\t$(MKDIRS) $@\n')
        f.flush()

    def write_extra(self, f): # tar, edit& browse
        f.write('.PHONY: tar\n')
        


def lst2str(flist):
    if type(flist) == str:
        return flist
    if type(flist[0]) == list:
        return '\n'.join([lst2str(line) for line in flist])
    return ' '.join(flist)

def dict_merge(main, extra):
    tmp = main.copy()
    tmp.update(extra)
    return tmp

def nths(lst, n=0):
    ret = []
    for item in lst:
        if type(item) == list and len(item) > n:
            ret.append(item[n])
    return ret

def addoptdep(deps, opts):
    opts = opts[:]
    if '|' not in deps:
        deps += ['|']
    if type(opts) != list:
        opts = [opts]
    for i in opts:
        if i in deps + ['']:
            opts.remove(i)
    deps += opts

def delrep(lst):
    try:
        lst = list(set(lst))
    except TypeError:
        pass
    return lst

def lstasdict(lst, key):
    for item in lst:
        if item[0] == key:
            return item
