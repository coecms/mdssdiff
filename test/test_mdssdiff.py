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

# Find the python libraries we're testing
sys.path.append('..')
sys.path.append('.')

from mdssdiff import diffdir

dirs = ["1","2","3"]
dirtree = os.path.join(*dirs)
print(dirtree)
paths = [ ["1","lala"], ["1","po"], ["1","2","Mickey"], ["1","2","Minny"], ["1","2","Pluto"], ["1","2","3","Ren"], ["1","2","3","Stimpy"] ]
remote = "remote"
dirtreeroot = dirs[0]
verbose=False

def touch(fname, times=None):
    # http://stackoverflow.com/a/1160227/4727812
    with open(fname, 'a'):
        os.utime(fname, times)

def setup_module(module):
    if verbose: print ("setup_module      module:%s" % module.__name__)
    try:
        shutil.rmtree(dirtreeroot)
        shutil.rmtree(remote)
    except:
        pass
    os.makedirs(dirtree)
    for p in paths:
        touch(os.path.join(*p))
    shutil.copytree(dirtreeroot, os.path.join(remote,dirtreeroot))
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    shutil.rmtree(dirtreeroot)
    shutil.rmtree(remote)

def test_diffdir():
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Remove a local file
    file = os.path.join(*paths[5])
    os.remove(file)
    if verbose: print('removing {}'.format(file))
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(missinglocal == [file])
    assert(len(missingremote) == 0)
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Remove same remote file
    if verbose: print('removing {}'.format(os.path.join(remote,file)))
    os.remove(os.path.join(remote,file))
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Remove a remote file
    file = os.path.join(*paths[3])
    os.remove(os.path.join(remote,file))
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(missingremote == [file])
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Remove same local file
    os.remove(file)
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Write 3 bytes into a local file
    file = os.path.join(*paths[2])
    fh = open(file,"wb")
    fh.write("\x5F\x9D\x3E")
    fh.close()
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(mismatched == [file])
    assert(mismatchedsizes == [(3,0)])

    # Write 3 bytes into same remote file
    fh = open(os.path.join(remote,file),"wb")
    fh.write("\x5F\x9D\x3E")
    fh.close()
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatched) == 0)
    assert(len(mismatchedsizes) == 0)

    # Write 4 bytes into same remote file
    fh = open(os.path.join(remote,file),"wb")
    fh.write("\x5F\x9D\x3E\x00")
    fh.close()
    missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(remote, dirtreeroot, mdsscmd="ls -l", recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(mismatched == [file])
    assert(mismatchedsizes == [(3,4)])
