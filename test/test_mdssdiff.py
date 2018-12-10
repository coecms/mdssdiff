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
import subprocess
import shlex
import datetime, time

from fnmatch import fnmatch

from mdssdiff.mdssdiff import diffdir, parse_args, main

import pdb #; pdb.set_trace()

dirs = ["1","2","3"]
dirtree = os.path.join(*dirs)
print(dirtree)
paths = [ ["1","lala"], ["1","po"], ["1","2","Mickey"], ["1","2","Minny"], ["1","2","Pluto"], ["1","2","3","Ren"], ["1","2","3","Stimpy"] ]
prefix = "test_mdss"
dirtreeroot = dirs[0]
verbose=3
project=os.environ.get('PROJECT','a12')

def touch(fname, times=None):
    # http://stackoverflow.com/a/1160227/4727812
    if times is not None:
        times = (times,times)
            
    with open(fname, 'a'):
        os.utime(fname, times)

def runcmd(cmd):
    subprocess.check_call(shlex.split(cmd),stderr=subprocess.STDOUT)

def setup_files():
    for p in paths:
        touch(os.path.join(*p))
    # shutil.copytree(dirtreeroot, os.path.join(remote,dirtreeroot))
    runcmd('mdss mkdir {}'.format(prefix))
    runcmd('mdss put -r {} {}'.format(dirs[0],prefix))

def setup_module(module):
    if verbose: print ("setup_module      module:%s" % module.__name__)
    try:
        shutil.rmtree(dirtreeroot)
    except:
        pass
    os.makedirs(dirtree)
    setup_files()
    
def test_diffdir():
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Remove a local file
    file = os.path.join(*paths[5])
    os.remove(file)
    if verbose: print('removing {}'.format(file))
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missinglocal == [file])
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Remove same remote file
    remotefile = os.path.join(prefix,file)
    if verbose: print('removing {}'.format(remotefile))
    runcmd('mdss -P {} rm {}'.format(project,remotefile))
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Remove a remote file
    file = os.path.join(*paths[3])
    remotefile = os.path.join(prefix,file)
    if verbose: print('removing {}'.format(remotefile))
    runcmd('mdss -P {} rm {}'.format(project,remotefile))
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missingremote == [file])
    assert(len(missinglocal) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Remove same local file
    os.remove(file)
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Write 3 bytes into a local file
    file = os.path.join(*paths[2])
    fh = open(file,"wb")
    fh.write(b"\x5F\x9D\x3E")
    fh.close()
    dt = datetime.datetime.now() - datetime.timedelta(days=1)
    touch(file,time.mktime(dt.timetuple()))
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(mismatchedsizes == {file : (3,0)})
    # The time may vary, but we can't know for sure, so we won't check this
    assert(mismatchedtimes)

def test_sync():

    # Syncing different sized file from previous test
    main(parse_args(shlex.split("-r -P {} -cr -f -p {} {}".format(project,prefix,dirs[0]))))

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # (re)Make a local file
    file = os.path.join(*paths[5])
    touch(file)

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missingremote == [ file ])
    assert(len(missinglocal) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Copy to remote
    main(parse_args(shlex.split("-r -P {} -cr -f -p {} {}".format(project,prefix,dirs[0]))))

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Remove same remote file
    remotefile = os.path.join(prefix,file)
    if verbose: print('removing {}'.format(remotefile))
    runcmd('mdss -P {} rm {}'.format(project,remotefile))

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missingremote == [ file ])
    assert(len(missinglocal) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Copy to remote
    main(parse_args(shlex.split("-r -P {} -cr -f -p {} {}".format(project,prefix,dirs[0]))))

    # Change the time
    dt = datetime.datetime.now() - datetime.timedelta(days=1)
    touch(file,time.mktime(dt.timetuple()))

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert((mismatchedtimes[file][1] - mismatchedtimes[file][0]) == datetime.timedelta(days=1))

    # Copy to remote
    main(parse_args(shlex.split("-r -P {} -cr -f -p {} {}".format(project,prefix,dirs[0]))))

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)

def test_filter():

    setup_files()

    pattern = '*M*'
    other_pattern = '*i*'
    files = []
    other_files = []

    for p in paths:
        file = os.path.join(*p)
        if fnmatch(file,pattern):
            files.append(file)
            print("Removing {}".format(file))
            os.remove(file)
        if fnmatch(file,other_pattern):
            other_files.append(file)

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missinglocal == files)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Should be no overlap between this filter and files removed above
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose, filter="*la*")
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose, filter=other_pattern)
    assert(missinglocal == sorted(list(set(files).intersection(other_files))))
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    setup_files()

    files = []
    other_files = []

    for p in paths:
        file = os.path.join(*p)
        if fnmatch(file,pattern):
            files.append(file)
            # Remove same remote file
            remotefile = os.path.join(prefix,file)
            if verbose: print('removing {}'.format(remotefile))
            runcmd('mdss -P {} rm {}'.format(project,remotefile))
        if fnmatch(file,other_pattern):
            other_files.append(file)

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose)
    assert(missingremote == files)
    assert(len(missinglocal) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    # Should be no overlap between this filter and files removed above
    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose, filter="*la*")
    assert(len(missinglocal) == 0)
    assert(len(missingremote) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)

    missinglocal, missingremote, mismatchedsizes, mismatchedtimes = diffdir(prefix, dirtreeroot, project, recursive=True, verbose=verbose, filter=other_pattern)
    assert(missingremote == sorted(list(set(files).intersection(other_files))))
    assert(len(missinglocal) == 0)
    assert(len(mismatchedsizes) == 0)
    assert(len(mismatchedtimes) == 0)
