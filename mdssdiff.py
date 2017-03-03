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

def diffdir(prefix, directory, mdsscmd="mdss ls -l", recursive=False, verbose=0):

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
            output = None
            if verbose > 0: print("Could not get listing from mdss for ",remotedir)
        if output is not None:
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
                if verbose > 1: print(fullpath,remotefile)
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

def remote_put(prefix, files, mdsscmd='mdss put', mdssmkdir='mdss mkdir', verbose=0):

    # Keep a list of remote directories that have been made
    remotedirs = set()
    for file in files:
        rfile = os.path.join(prefix,file)
        rdir = os.path.dirname(rfile)
        # Check if we need to make a remote directory in which to put our files
        if rdir not in remotedirs:
            cmd = shlex.split(mdssmkdir)
            cmd.append(rdir)
            if verbose > 0: print(" ".join(cmd))
            try:
                subprocess.check_call(cmd,stderr=subprocess.STDOUT)
            except:
                if verbose > 0: print("Could not make remote directory ",rdir)
            else:
                # Add remote directory to set so not made again
                remotedirs.add(rdir)
        cmd = shlex.split(mdsscmd)
        cmd.extend((file,rfile))
        if verbose > 1: print(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
        except:
            if verbose: print("Could not copy ",file," to remote location: ",os.path.join(prefix,file))

def remote_get(prefix, files, mdsscmd='mdss get -r', verbose=False):

    for file in files:
        cmd = shlex.split(mdsscmd)
        cmd.append(os.path.join(prefix,file),file)
        if verbose > 1: print(cmd)
        try:
            output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
        except:
            if verbose > 0: print("Could not copy ",file," from remote location: ",os.path.join(prefix,file))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Compare local directories and those on mdss. Report differences")
    parser.add_argument("-v","--verbose", help="Increase verbosity", action='count', default=0)
    parser.add_argument("-p","--pathprefix", help="Prefix for mdss path")
    parser.add_argument("-r","--recursive", help="Recursively descend directories (default False)", action='store_true')
    #
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-cr","--copyremote", help="Copy over files that are missing on remote (False)", action='store_true')
    group.add_argument("-cl","--copylocal", help="Copy over files that are missing on local (False)", action='store_true')
    #
    parser.add_argument("-f","--force", help="Force copying of different sized files, following --cr or --cl (False)", action='store_true')
    parser.add_argument("inputs", help="netCDF files or directories (-r must be specified to recursively descend directories)", nargs='+')
    args = parser.parse_args()

    if args.pathprefix is not None:
        prefix = args.pathprefix
    else:
        prefix = '.'

    verbose = args.verbose

    for directory in args.inputs:

        if os.path.isdir(directory):

            missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(prefix, directory, recursive=args.recursive, verbose=args.verbose)

            if len(missinglocal) > 0:
                if args.copylocal:
                    remote_get(prefix,missinglocal,verbose=args.verbose)
                else:
                    print("Missing on local filesystem:")
                    for file in missinglocal:
                        print(file)
    
            if len(missingremote) > 0:
                if args.copyremote:
                    remote_put(prefix,missingremote,verbose=args.verbose)
                else:
                    print("Missing on remote filesystem:")
                    for file in missingremote:
                        print(file)
    
            if len(mismatched) > 0:
                if args.copyremote and args.force:
                    remote_put(prefix,mismatched,verbose=args.verbose)
                elif args.copylocal and args.force:
                    remote_get(prefix,mismatched,verbose=args.verbose)
                else:
                    print("Size does not match:")
                    for file, (size, size_orig) in izip(mismatched, mismatchedsizes):
                        print("{} local: {} remote: {}".format(file, size, size_orig))
        else:
            print("Skipping {} :: not a directory".format(directory))
