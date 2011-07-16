#!/usr/bin/env python

import os
import sys
import re
import json
import cli
import crmakebase

Targets = {}

Makefiles = {}

AllFiles = []

def rd_config():
    try:
        conf_txt = open('crmake.in').read()
    except IOError:
        return
    conf = eval(conf_txt)
    if 'name' in conf and type(conf['name']) == list:
        for target in conf['name']:
            if target['name'] == 'main':
                continue
            Targets[target['name']] = target
        conf.pop('name')
    Targets['main'] = conf

#inh ##TODO(Vars)

def cmplt_conf(): pass

def chk_config():
    for tgt in Targets:
        if 'type' not in Targets[tgt]:
            exit(1)

def crt_mklst():
    for tgt, conf in Targets.items():
        makeclass = get_class(conf['type'])
        Makefiles[tgt] = makeclass()
        Makefiles[tgt].add_config(conf)

def dist_files(flst):
    for src in flst:
        parent = Makefiles['main']
        for name, make in Makefiles.items():
            if cli.ischild(make.crvar['src'], src) or \
                    cli.ischild(make.crvar['src'], parent.crvar['src']):
                continue
            parent = make
        parent.add_avail_f(src)

def prepare():
    for name, make in Makefiles.items():
        make.get_f_list()
        make.get_data_f()
        make.classify_files()
        make.pre_vars()
        make.get_ndirs()
        make.torel()
    dist_fnames()

def dist_fnames(): pass

def writes():
    for name, make in Makefiles.items():
        make.write()


Classes = {'base': [crmakebase, {'makebase': crmakebase.makebase}]}
def get_class(typ):
    if typ[0] in Classes:
        module = Classes[typ[0]]
    else:
        module = [__import__('crmake_' + typ[0]), {}]
        Classes[typ[0]] = module
    if typ[1] in module[1]:
        return module[1][typ[1]]
    makeclass = getattr(module[0], typ[1] + '_make')
    module[1][typ[1]] = makeclass
    return makeclass

def main():
    rd_config()
    chk_config()
    cmplt_conf()
    crt_mklst()
    AllFiles = cli.find('.')
    dist_files(AllFiles)
    prepare()
    writes()

if __name__ == '__main__':
    main();
