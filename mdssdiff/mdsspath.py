from __future__ import unicode_literals

import os
import errno
import sys
import shlex
import subprocess
import datetime
import time
import re
import datetime
from six import StringIO

_calmonths = dict( (x, i+1) for i, x in
                   enumerate(('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')) )

_mdss_ls_cmd    = 'mdss -P {} dmls -l'
_mdss_put_cmd   = 'mdss -P {} put'
_mdss_get_cmd   = 'mdss -P {} get'
_mdss_mkdir_cmd = 'mdss -P {} mkdir'
_mdss_rm_cmd    = 'mdss -P {} rm'
_mdss_rmdir_cmd = 'mdss -P {} rmdir'

def walk(top, project, topdown=True, onerror=None):
    """
    Generator that yields tuples of (root, dirs, nondirs).

    Adapted from http://code.activestate.com/recipes/499334-remove-ftp-directory-walk-equivalent/
    """

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        dirs, nondirs, _, _ = mdss_listdir(top, project)
    except os.error as err:
        if onerror is not None:
            onerror(err)
        return

    if topdown:
        yield top, dirs, nondirs
    for dname in dirs:
        # This would break on non-POSIX compliant systems, but AFAIK mdss
        # is not accessible from anything but unix (POSIX) machines.
        path = os.path.join(top, dname)
        # Don't check for links, as walk does not identify links as directories
        for x in walk(path, project, topdown, onerror):
            yield x
    if not topdown:
        yield top, dirs, nondirs

def mdss_ls(path,project,options=None):
    cmd = shlex.split(_mdss_ls_cmd.format(project))
    if options is not None:
        cmd.extend(options)
    cmd.append(path)
    try:
        output = subprocess.check_output(cmd,stderr=subprocess.STDOUT).decode('utf-8')
    except:
        output = ''
    return(output)

def mdss_listdir(path, project):
    """
    List the contents of the mdss path and return two tuples of filenames
    one for subdirectories, and one for non-directories (normal files and other
    stuff). 
    Adapted from http://code.activestate.com/recipes/499334-remove-ftp-directory-walk-equivalent/
    """
    dirs, nondirs, sizes, times = [], [], [], []
    listing = mdss_ls(path,project)

    for line in StringIO(listing):
        # Parse, assuming a UNIX listing
        if line.startswith("total"): continue
        # Remove trailing newline (and whitespace)
        line = line.rstrip()
        words = line.split(None, 8)
        if len(words) < 6:
            print >> sys.stderr, 'Warning: Error reading short line', line
            continue

        # Get the filename.
        filename = words[-1].lstrip()
        if filename in ('.', '..'):
            continue

        if isdir(line):
            dirs.append(filename)
        else:
            nondirs.append(filename)
            sizes.append(getsize(line))
            times.append(getmtime(line))

    return dirs, nondirs, sizes, times

def mdss_mkdir(dir, project, verbose=0):
    cmd = shlex.split(_mdss_mkdir_cmd.format(project))
    cmd.append(dir)
    if verbose > 1: print(" ".join(cmd))
    subprocess.check_call(cmd,stderr=subprocess.STDOUT)

def remote_put(prefix, files, project, verbose=0):

    if not isinstance(files, list):
        files = [files]

    for file in files:
        rfile = os.path.join(prefix,file)
        rdir = os.path.dirname(rfile)
        # Check if we need to make a remote directory in which to put our files
        if not isdir(rdir, project):
            mdss_mkdir(rdir, project)
        cmd = shlex.split(_mdss_put_cmd.format(project))
        cmd.extend((file,rfile))
        if verbose > 0: print(file)
        if verbose > 1: print(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
        except:
            if verbose: print("Could not copy ",file," to remote location: ",os.path.join(prefix,file))

def remote_get(prefix, files, project, verbose=0):

    if not isinstance(files, list):
        files = [files]

    for file in files:
        # Make sure there is a destination directory
        mkdir_p(os.path.dirname(file))
        cmd = shlex.split(_mdss_get_cmd.format(project))
        cmd.extend([os.path.join(prefix,file),file])
        if verbose > 0: print(file)
        if verbose > 1: print(cmd)
        try:
            output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
        except:
            if verbose > 0: print("Could not copy ",file," from remote location: ",os.path.join(prefix,file))

def mkdir_p(path):
    # http://stackoverflow.com/a/600612
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def isfile(path,project=None):
    """Return true if the pathname refers to an existing directory."""
    if ismode(path,'-',project):
        return True
    else:
        return False

def isdir(path,project=None):
    """Return true if the pathname refers to an existing directory."""
    if ismode(path,'d',project):
        return True
    else:
        return False

def islink(path,project=None):
    """Return true if the pathname refers to an existing directory."""
    if ismode(path,'l',project):
        return True
    else:
        return False

def ismode(path,mode,project=None):
    """Return true if the mode of path equals mode specified."""
    if getmode(path,project) == mode:
        return True
    else:
        return False

def getmode(path,project=None):
    """Return true if the pathname refers to an existing directory."""
    line = getls(path,project)
    return line[0] if len(line) > 0 else ''

def getsize(path,project=None):
    """Return the size of a file parsed from listing."""
    line = getls(path,project)
    words = line.split(None, 8)
    if len(words) < 7:
        return None
    else:
        try:
            size = int(words[4])
        except ValueError:
            return None
        else:
            return size

def getls(path,project=None):    
    """If no project path is assumed to be a unix line listing, otherwise
    get listing"""
    if project is None:
        line = path
    else:
        line = mdss_ls(path,project,['-d']).rstrip()
    return line

def getmtime(path,project=None):
    """Return last modification time of a file parsed from listing as 
    datetime object to minute precision."""
    line = getls(path,project)
    words = line.split(None, 8)
    if len(words) < 6:
        return None

    # Get the date.
    return datetime.datetime.strptime("{} {}".format(words[5],words[6]), "%Y-%m-%d %H:%M" )

def localmtime(path):
    """Return last modification time given the path to a file on the
    local file system. Returned as datetime object with minute precision
    to match time resolution available from mdss."""

    dt = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)

    # return dt - datetime.timedelta(seconds=dt.second,microseconds=dt.microsecond)
    return dt.replace(second=0,microsecond=0)

