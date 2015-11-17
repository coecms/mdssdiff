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

import os
import subprocess
import argparse
import shlex
from itertools import izip

# supported_file_types = ('-','b','c','C')

def diffdir(prefix, directory, mdsscmd="mdss ls -l", recursive=False, verbose=False):

    missinglocal = []; missingremote = []; mismatched = []; mismatchedsizes = []

    for root, dirs, files in os.walk(directory):
        if (root != directory and not recursive):
            print("Skipping subdirectories of {0} :: recursive option not specified".format(directory))
            break
        remoteinfo = {}
        remotedir = os.path.join(prefix,root)
        cmd = shlex.split(mdsscmd)
        cmd.append(remotedir)
        try:
            output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
        except:
            print("Could not get listing from mdss for ",remotedir)
            raise
        for line in output.splitlines():
            try:
                flags, links, user, group, size, month, day, year, path = line.split()
            except:
                continue
                # print("Could not parse mdss file listing: ",remotefile)
            # Ignore directories
            if not flags.startswith('d'):
                remoteinfo[path] = int(size)
        for file in files:
            fullpath = os.path.join(root,file)
            if file in remoteinfo:
                remotefile = os.path.join(prefix,fullpath)
                if verbose: print(fullpath,remotefile)
                size_orig = os.path.getsize(fullpath)
                if size_orig != remoteinfo[file]:
                    mismatched.append(fullpath)
                    mismatchedsizes.append((size_orig,remoteinfo[file]))
                del(remoteinfo[file])
            else:
                missingremote.append(fullpath)
        for file in remoteinfo.keys():
            fullpath = os.path.join(root,file)
            missinglocal.append(fullpath)
    return missinglocal, missingremote, mismatched, mismatchedsizes

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Compare local directories and those on mdss. Report differences")
    parser.add_argument("-v","--verbose", help="Verbose output", action='store_true')
    parser.add_argument("-p","--pathprefix", help="Prefix for mdss path")
    parser.add_argument("-r","--recursive", help="Recursively descend directories (default False)", action='store_true')
    parser.add_argument("inputs", help="netCDF files or directories (-r must be specified to recursively descend directories)", nargs='+')
    args = parser.parse_args()

    if args.pathprefix is not None:
        prefix = args.pathprefix
    else:
        prefix = '.'

    verbose = args.verbose

    for directory in args.inputs:

        missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(prefix, directory, recursive=args.recursive, verbose=args.verbose)

        if len(missinglocal) > 0:
            print("Missing on local filesystem:")
            for file in missinglocal:
                print(file)

        if len(missingremote) > 0:
            print("Missing on remote filesystem:")
            for file in missingremote:
                print(file)

        if len(mismatched) > 0:
            print("Size does not match:")
            for file, (size, size_orig) in izip(mismatched, mismatchedsizes):
                print("{} remote: {} local: {}".format(file, size, size_orig))
