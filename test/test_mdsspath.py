#!/usr/bin/env python

"""
Copyright 2015 ARC Centre of Excellence for Climate Systems Science

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from __future__ import print_function

import pytest
import sys
import os
import shutil
import shlex
import subprocess

# Find the python libraries we're testing
sys.path.append('..')
sys.path.append('.')

import mdsspath
import mdssdiff

dirs = ["1","2","3"]
dirtree = os.path.join(*dirs)
paths = [ ["1","lala"], ["1","po"], ["1","2","Mickey"], ["1","2","Minny"], ["1","2","Pluto"], ["1","2","3","Ren"], ["1","2","3","Stimpy"] ]
remote = "remote"
dirtreeroot = dirs[0]
verbose=False
prefix='test_mdss'
project=os.environ['PROJECT']

# Test if we have a working mdss to connect to
try:
    mdsspath.mdss_ls(".",project)
except:
    # Monkey-patch to use local file commands if we don't
    print("\n\n!!! No mdss: Monkey patching to use local commands !!!\n")
    mdsspath._mdss_ls_cmd    = 'ls -l'
    mdsspath._mdss_put_cmd   = 'cp'
    mdsspath._mdss_get_cmd   = 'cp'
    mdsspath._mdss_mkdir_cmd = 'mkdir'
    mdsspath._mdss_rm_cmd    = 'rm'

def touch(fname, times=None):
    # http://stackoverflow.com/a/1160227/4727812
    with open(fname, 'a'):
        os.utime(fname, times)

def runcmd(cmd):
    subprocess.check_call(shlex.split(cmd),stderr=subprocess.STDOUT)

def setup_module(module):
    if verbose: print ("setup_module      module:%s" % module.__name__)
    try:
        shutil.rmtree(dirtreeroot)
    except:
        pass
    os.makedirs(dirtree)
    for p in paths:
        touch(os.path.join(*p))

    # Write 3 bytes into a local file
    file = os.path.join(*paths[2])
    fh = open(file,"wb")
    fh.write("\x5F\x9D\x3E")
    fh.close()

    # shutil.copytree(dirtreeroot, os.path.join(remote,dirtreeroot))
    # Make our top level directory
    runcmd(" ".join([mdsspath._mdss_mkdir_cmd.format(project),prefix]))
    # Copy files into it
    runcmd(" ".join([mdsspath._mdss_put_cmd.format(project),'-r',dirs[0],prefix]))
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    shutil.rmtree(dirtreeroot)
    runcmd(" ".join([mdsspath._mdss_rm_cmd.format(project),'-r',prefix]))

def test_integrity():

    assert(os.path.isdir(dirs[0]))
    assert(mdsspath.mdss_listdir(os.path.join(prefix,dirs[0]),project) == (['2'], ['lala', 'po']))
    assert(mdsspath.getsize(os.path.join(prefix,*paths[2]),project) == 3)
    
def test_get():

    # Testing slightly out of order, but it is very useful to use it here so I will
    listinglocal = mdssdiff.getlisting(dirs[0],recursive=True)
    for file in listinglocal:
        # print(file)
        assert(os.path.isfile(file))
    # This will (indirectly) test mdsspath.walk
    listingremote = mdssdiff.getlisting(os.path.join(prefix,dirs[0]),project,recursive=True)
    for file in listingremote:
        # print(file)
        assert(mdsspath.isfile(file,project))
        assert(os.path.relpath(file,prefix) in listinglocal)

    missingfile = listinglocal.pop()
    os.remove(missingfile)
    mdsspath.remote_get(prefix, missingfile, project)
    assert(os.path.isfile(missingfile))

def test_put():

    newfile = os.path.join(dirtree,'newfile')
    touch(newfile)
    mdsspath.remote_put(prefix, newfile, project)
    mdsspath.remote_get(prefix, newfile, project)
    assert(os.path.isfile(newfile))



