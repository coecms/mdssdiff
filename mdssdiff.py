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

import mdsspath

def walk(path,project=None):
    if project is None:
        return os.walk(path)
    else:
        return mdsspath.walk(path,project)

def getlisting(path,project=None,recursive=False,verbose=0):

    listing = set() 

    for (dname, dirnames, filenames) in walk(path,project):

        if (verbose > 0): print("Walking directory {}".format(dname))

        if (dname != path and not recursive):
            print("Skipping subdirectories of {0} :: recursive option not specified".format(dname))
            break
    
        if (verbose > 1): print("Adding files{}".format(filenames))
        for file in filenames:
            listing.add(os.path.join(dname,file))

    return listing

def makepath(path,files):

    listing = []

    for file in files:
        listing.append(os.path.join(path,file))

    return listing

# supported_file_types = ('-','b','c','C')

def diffdir(prefix, directory, project, recursive=False, verbose=0):

    missinglocal = []; missingremote = []; mismatched = []; mismatchedsizes = []

    visited = set()

    # Walk local directory tree and compare to remore directory tree
    for (dname, dirnames, filenames) in walk(directory):

        if (verbose > 0): print("Walking local directory {}".format(dname))

        if (dname != directory and not recursive):
            print("Skipping subdirectories of {0} :: recursive option not specified".format(dname))
            break

        visited.add(dname)

        localset = set(filenames)
        rdname = os.path.join(prefix,dname)
        _, rfiles, rsizes = mdsspath.mdss_listdir(rdname,project,returnsize=True)
        remoteset = dict(izip(rfiles,rsizes))

        for file in localset:
            localfile = os.path.join(dname,file)
            if file in remoteset:
                remotefile = os.path.join(rdname,file)
                localsize = os.path.getsize(localfile)
                # remotesize = mdsspath.getsize(remotefile,project)
                remotesize = remoteset[file]
                if (verbose > 2): print("File: {} sizes: {} (l) {} (r)".format(localfile,localsize,remotesize))
                if localsize != remotesize:
                    if (verbose > 1): print("File: {} sizes differ: {} (l) {} (r)".format(localfile,localsize,remotesize))
                    mismatched.append(localfile)
                    mismatchedsizes.append((localsize,remotesize))
                del(remoteset[file])
            else:
                missingremote.append(localfile)
    
        missinglocal.extend(makepath(dname,remoteset.keys()))

    rdirectory = os.path.join(prefix,directory)
    
    # Now walk the remote directory structure to see if we've missed any directories that
    # are present locally
    for (rdname, rdirnames, rfilenames) in walk(rdirectory,project=project):

        ldirectory = os.path.relpath(rdname,prefix)

        if (verbose > 0): print("Walking remote directory {}".format(rdname))

        if (ldirectory != directory and not recursive):
            print("Skipping subdirectories of {0} :: recursive option not specified".format(dname))
            break

        if ldirectory not in visited:
            if (verbose > 0): print("Directory {} not found locally, adding files".format(ldirectory))
            missinglocal.extend([os.path.join(ldirectory,file) for file in rfilenames])

    return(missinglocal, missingremote, mismatched, mismatchedsizes)
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Compare local directories and those on mdss. Report differences")
    parser.add_argument("-v","--verbose", help="Increase verbosity", action='count', default=0)
    parser.add_argument("-P","--project", help="Project code for mdss (default to $PROJECT)")
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

    if args.project is None:
        project = os.environ['PROJECT']
    else:
        project = args.project

    for directory in args.inputs:

        if os.path.isdir(directory):

            missinglocal, missingremote, mismatched, mismatchedsizes = diffdir(prefix, directory, project, recursive=args.recursive, verbose=args.verbose)

            if len(missinglocal) > 0:
                if args.copylocal:
                    print("Copying to local filesystem:")
                    mdsspath.remote_get(prefix,missinglocal,project,verbose=args.verbose)
                else:
                    print("Missing on local filesystem:")
                for file in missinglocal:
                    print(file)
    
            if len(missingremote) > 0:
                if args.copyremote:
                    print("Copying to remote filesystem:")
                    mdsspath.remote_put(prefix,missingremote,project,verbose=args.verbose)
                else:
                    print("Missing on remote filesystem:")
                for file in missingremote:
                    print(file)
    
            if len(mismatched) > 0:
                print("Size does not match:")
                for file, (size, size_orig) in izip(mismatched, mismatchedsizes):
                    print("{} local: {} remote: {}".format(file, size, size_orig))
                if args.force:
                    if args.copyremote:
                        print("Copying to remote filesystem")
                        mdsspath.remote_put(prefix,mismatched,project,verbose=args.verbose)
                    elif args.copylocal:
                        print("Copying to local filesystem")
                        mdsspath.remote_get(prefix,mismatched,project,verbose=args.verbose)
                    else:
                        print("Option to force copying (--force) given, but neither -cr nor -cl specified")
        else:
            print("Skipping {} :: not a directory".format(directory))
