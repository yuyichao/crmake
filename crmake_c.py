#!/usr/bin/env python

import re
import crmakebase as base
import cli

class c_make(base.makebase):
    MakeVar = base.dict_merge(base.makebase.MakeVar,
                          {'CC': ['gcc'],
                           'CXX': ['g++'],
                           'LD': ['g++'],
                           'AR': ['ar'],
                           'CFLAGS': ['-fPIC', '-Wall'],
                           'CXXFLAGS': ['-fPIC', '-Wall'],
                           'SHAREDFLAGS': ['-shared'],
                           'OPTFLAGS': ['-O2'],
                           'DBGFLAGS': ['-g'],
                           'MODULES': [],
                           'BIN_DIR': 'bin',
                           'OBJ_DIR': 'obj'
                           })
    CrVar = base.dict_merge(base.makebase.CrVar, {'type': ['c', 'c', 'pro'],
                                                  'includepath': set()
                                                  })
    InstlDir = base.dict_merge(base.makebase.InstlDir, {'bindir': '$(PREFIX)/bin/'})
    fullname = re.compile('\\.(c|cpp|h)$')
    def __init__(self):
        base.makebase.__init__(self)
        self.clist = []
        self.cxxlist = []
        self.hlist = []
        self.olist = []
        self.dbgolist = []

    def classify_files(self):
        for f in self.flist:
            if f[-2:] == '.h':
                self.hlist.append(f)
            if f[-2:] == '.c':
                self.clist.append(f)
            if f[-4:] == '.cpp':
                self.cxxlist.append(f)

    def pre_vars(self):
        self.include_list()
        self.nmltgts()
        self.dbgtgts()
        self.run_tgt()

    def include_list(self):
        for h in self.hlist:
            self.crvar['includepath'].add(cli.dirname(h))
        for I in self.crvar['includepath']:
            self.makevar['CFLAGS'] += ['-I' + I]
            self.makevar['CXXFLAGS'] += ['-I' + I]

    def nmltgts(self):
        self.invar['C_TARGET'] = self.crvar['targets'][0] #TODO guess name
        self.rtgts['$(BIN_DIR)/$(C_TARGET)'] = {'deps': [], 'cmd': ['\t', '$(LD)', '$$(pkg-config --libs $(MODULES) 2> /dev/null)', '$(OPTFLAGS)', '$^', '-o', '$@']}
        self.targets[0][1] = ['$(BIN_DIR)/$(C_TARGET)']
        self.instl_target['$(BIN_DIR)/$(C_TARGET)'] = ['bin', 0o755]
        c2o = re.compile('\\.c$|\\.cpp$')
        drt = re.compile('\\\\\n|\n$', re.S)
        for c in self.clist:
            [ret, out, err] = cli.asystem(['gcc', '-MM', c] + self.makevar['CFLAGS'])#TODO
            if err:
                print(err)
                exit(ret)
            ofile = '$(OBJ_DIR)' + '/' + c2o.sub('.o', c)
            self.rtgts[ofile] = {'deps': [drt.sub('', out.split(':', 1)[1])],
                'cmd': ['\t', '$(CC)', '$$(pkg-config --cflags $(MODULES))',
                        '$(OPTFLAGS)', '$(CFLAGS)', '-c', '$<', '-o', '$@']}
            self.rtgts['$(BIN_DIR)/$(C_TARGET)']['deps'].append(ofile)
        for cxx in self.cxxlist:
            [ret, out, err] = cli.asystem(['gcc', '-MM', c] + self.makevar['CXXFLAGS'])#TODO
            if err:
                print(err)
                exit(ret)
            ofile = '$(OBJ_DIR)' + '/' + c2o.sub('.o', c)
            self.rtgts[ofile] = {'deps': [drt.sub('', out.split(':', 1)[1])],
                'cmd': ['\t', '$(CXX)', '$$(pkg-config --cflags $(MODULES))',
                        '$(OPTFLAGS)', '$(CXXFLAGS)', '-c', '$<', '-o', '$@']}
            self.rtgts['$(BIN_DIR)/$(C_TARGET)']['deps'].append(ofile)

    def dbgtgts(self):
        self.c_dbg_target = '$(C_TARGET)_debug'
        self.rtgts['$(BIN_DIR)/' + self.c_dbg_target] = {'deps': [], 'cmd': ['\t', '$(LD)', '$$(pkg-config --libs $(MODULES) 2> /dev/null)', '$(DBGFLAGS)', '$^', '-o', '$@']}
        self.targets.append(['debug', ['$(BIN_DIR)/' + self.c_dbg_target]])
        c2o = re.compile('\\.c$|\\.cpp$')
        drt = re.compile('\\\\\n|\n$', re.S)
        for c in self.clist:
            [ret, out, err] = cli.asystem(['gcc', '-MM', c] + self.makevar['CFLAGS'])#TODO
            if err:
                print(err)
                exit(ret)
            ofile = '$(OBJ_DIR)' + '/' + c2o.sub('_debug.o', c)
            self.rtgts[ofile] = {'deps': [drt.sub('', out.split(':', 1)[1])],
                'cmd': ['\t', '$(CC)', '$$(pkg-config --cflags $(MODULES))',
                        '$(DBGFLAGS)', '$(CFLAGS)', '-c', '$<', '-o', '$@']}
            self.rtgts['$(BIN_DIR)/' + self.c_dbg_target]['deps'].append(ofile)
        for cxx in self.cxxlist:
            [ret, out, err] = cli.asystem(['gcc', '-MM', c] + self.makevar['CXXFLAGS'])#TODO
            if err:
                print(err)
                exit(ret)
            ofile = '$(OBJ_DIR)' + '/' + c2o.sub('_debug.o', c)
            self.rtgts[ofile] = {'deps': [drt.sub('', out.split(':', 1)[1])],
                'cmd': ['\t', '$(CXX)', '$$(pkg-config --cflags $(MODULES))',
                        '$(DBGFLAGS)', '$(CXXFLAGS)', '-c', '$<', '-o', '$@']}
            self.rtgts['$(BIN_DIR)/' + self.c_dbg_target]['deps'].append(ofile)

    def run_tgt(self):
        self.targets.append(['run', ['$(BIN_DIR)/$(C_TARGET)_debug'], ['\t', '$<']])
        self.targets.append(['rdbg', ['$(BIN_DIR)/$(C_TARGET)_debug'], ['\t', 'gdb', '$<']])


