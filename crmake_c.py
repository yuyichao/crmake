#!/usr/bin/env python

import crmakebase as base

class c_make(base.makebase):
    MakeVar = base.dict_merge(base.makebase.MakeVar,
                          {'CC': ['gcc'],
                           'CXX': ['g++'],
                           'LD': ['g++'],
                           'AR': ['ar'],
                           'CFLAGS': ['-fPIC', '-Wall'],
                           'CXXFLAGS': ['-fPIC', '-Wall'],
                           'SHAREDFLAGS': ['-shared'],
                           
                           })
