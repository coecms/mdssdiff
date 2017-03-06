import os
import sys
import shlex
import subprocess
import StringIO
import datetime
import time
import re

try:
    import cStringIO
    StringIO = cStringIO
except ImportError:
    import StringIO
    
_calmonths = dict( (x, i+1) for i, x in
                   enumerate(('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')) )

def walk(project, top, topdown=True, onerror=None):
    """
    Generator that yields tuples of (root, dirs, nondirs).
    """

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        dirs, nondirs = _mdss_listdir(project,top)
    except os.error, err:
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
        for x in walk(project, path, topdown, onerror):
            yield x
    if not topdown:
        yield top, dirs, nondirs

def _mdss_ls(project,path,options=None):
    cmd = shlex.split('mdss -P {} ls -l'.format(project))
    if options is not None:
        cmd.extend(options)
    cmd.append(path)
    try:
        output = subprocess.check_output(cmd,stderr=subprocess.STDOUT)
    except:
        output = None
    return(output)

def _mdss_listdir(project,path):
    """
    List the contents of the mdss path and return two tuples of filenames
    one for subdirectories, and one for non-directories (normal files and other
    stuff). 
    """
    dirs, nondirs = [], []
    listing = _mdss_ls(project,path)

    for line in StringIO.StringIO(listing):
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

        # Get the type
        mode = words[0]

        if mode[0] == 'd':
            dirs.append(filename)
        else:
            nondirs.append(filename)

    return dirs, nondirs

def isfile(project,path):
    """Return true if the pathname refers to an existing directory."""
    if ismode(project,path,'-'):
        return True
    else:
        return False

def isdir(project,path):
    """Return true if the pathname refers to an existing directory."""
    if ismode(project,path,'d'):
        return True
    else:
        return False

def islink(project,path):
    """Return true if the pathname refers to an existing directory."""
    if ismode(project,path,'l'):
        return True
    else:
        return False

def ismode(project,path,mode):
    """Return true if the mode of path equals mode specified."""
    if getmode(project,path) == mode:
        return True
    else:
        return False

def getmode(project,path):
    """Return true if the pathname refers to an existing directory."""
    line = _mdss_ls(project,path,['-d'])
    return line[0]

def getsize(project,path):
    """Return the size of a file parsed from listing."""
    line = _mdss_ls(project,path)
    line = line.rstrip()
    words = line.split(None, 8)
    if len(words) < 6:
        return None
    else:
        return int(words[4])

def getmtime(project,path):
    """Return the last modification time of a file parsed from listing.
    This is potentially spectacularly inaccurate, as times older than 6 months
    have only year/month/day and no time of day information."""

    line = _mdss_ls(project,path,['-d'])
    line = line.rstrip()
    words = line.split(None, 8)
    if len(words) < 6:
        return None

    # Get the date.
    year = datetime.datetime.today().year
    month = _calmonths[words[5]]
    day = int(words[6])
    mo = re.match('(\d+):(\d+)', words[7])
    if mo:
        hour, min = map(int, mo.groups())
    else:
        mo = re.match('(\d\d\d\d)', words[7])
        if mo:
            year = int(mo.group(1))
            hour, min = 0, 0
        else:
            raise ValueError("Could not parse time/year in line: '%s'" % line)
    dt = datetime.datetime(year, month, day, hour, min)
    return time.mktime(dt.timetuple())

def _mdss_fulllistdir(project,path):
    """
    List the contents of the mdss path and return two tuples of

       (filename, size, mtime, mode, link)

    one for subdirectories, and one for non-directories (normal files and other
    stuff).  If the path is a symbolic link, 'link' is set to the target of the
    link (note that both files and directories can be symbolic links).
    """
    dirs, nondirs = [], []
    listing = _mdss_ls(project,path)

    for line in StringIO.StringIO(listing):
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

        # Get the type and mode.
        mode = words[0]

        extra = None
        # Get the link target, if the file is a symlink.
        if mode[0] == 'l':
            i = filename.find(" -> ")
            if i >= 0:
                extra = filename[i+4:]
                filename = filename[:i]

        # Get the file size.
        size = int(words[4])

        # Get the date.
        year = datetime.datetime.today().year
        month = _calmonths[words[5]]
        day = int(words[6])
        mo = re.match('(\d+):(\d+)', words[7])
        if mo:
            hour, min = map(int, mo.groups())
        else:
            mo = re.match('(\d\d\d\d)', words[7])
            if mo:
                year = int(mo.group(1))
                hour, min = 0, 0
            else:
                raise ValueError("Could not parse time/year in line: '%s'" % line)
        dt = datetime.datetime(year, month, day, hour, min)
        mtime = time.mktime(dt.timetuple())

        entry = (filename, size, mtime, mode, extra)
        if mode[0] == 'd':
            dirs.append(entry)
        else:
            nondirs.append(entry)

    return dirs, nondirs

