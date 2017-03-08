# mdssdiff
Look for differences between local filesystem and it's copy on a mass data store system

[![Build Status](https://travis-ci.org/coecms/mdssdiff.svg?branch=master)](https://travis-ci.org/coecms/mdssdiff)
[![codecov.io](https://codecov.io/github/coecms/mdssdiff/coverage.svg?branch=master)](https://codecov.io/github/coecms/mdssdiff?branch=master)
[![Code Health](https://landscape.io/github/coecms/mdssdiff/master/landscape.svg?style=flat)](https://landscape.io/github/coecms/mdssdiff/master)

To use:

```
module purge
module use ~access/modules
module load mdssdiff
```

Basic usage message:
```
mdssdiff -h
usage: mdssdiff [-h] [-v] [-P PROJECT] [-p PATHPREFIX] [-r] [-cr | -cl] [-f]
                   inputs [inputs ...]

Compare local directories and those on mdss. Report differences

positional arguments:
  inputs                netCDF files or directories (-r must be specified to
                        recursively descend directories)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity
  -P PROJECT, --project PROJECT
                        Project code for mdss (default to $PROJECT)
  -p PATHPREFIX, --pathprefix PATHPREFIX
                        Prefix for mdss path
  -r, --recursive       Recursively descend directories (default False)
  -cr, --copyremote     Copy over files that are missing on remote (False)
  -cl, --copylocal      Copy over files that are missing on local (False)
  -f, --force           Force copying of different sized files, following --cr
                        or --cl (False)

```

For example, say you have a personal directory on mdss:
```
mdss ls -ld personal/me
drwxrws--- 4 abc123 a00 92 Dec 14  2014 personal/me
```
And you have used mdss to put another directory there
```
mdss put -r data personal/me/
mdss ls -ld personal/me/data
-rw-r--r-- 1 abc123 a00  1219 Nov  9 12:40 personal/me/data
```
To check if all the files have been correctly copied:
```
mdssdiff -p personal/me data
```
This will show a list of which files are present/absent on the local or remote (mdss) filesystem. It 
will also notify show any files which differ in size.

To recursively descend directories to check for differences used the
`-r` flag
```
mdssdiff -p personal/me -r data
```

This will also work the other way, and tell you if there are files on
the remote system that are not present locally.

If there are files in your local directory that are not on the mdss,
say you made some new ones or your last mdss copy command failed to
complete cleanly, and you wish to copy them to mdss you can use
the `--copyremote/-cr` flag:
```
mdssdiff -p personal/me -r -cr data
```

Equally, if you have deleted some files in your local directory that
you wish to copy back from mdss you can use the `--copyremote/-cr`
flag:
```
mdssdiff -p personal/me -r -cr data
```

If there are files of unequal size you must specify `-f/--force` to
force copying the files, and in this case the decision of which way
the copy will go (from or to mdss) depends on specifying either of the `-cr`
or `-cl` options. e.g. to copy files of different size *from* the local
directory *to* mdss
```
mdssdiff -p personal/me -r -cr data
```
