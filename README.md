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
usage: mdssdiff [-h] [-v] [-p PATHPREFIX] [-r] inputs [inputs ...]

Compare local directories and those on mdss. Report differences

positional arguments:
  inputs                netCDF files or directories (-r must be specified to
                        recursively descend directories)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output
  -p PATHPREFIX, --pathprefix PATHPREFIX
                        Prefix for mdss path
  -r, --recursive       Recursively descend directories (default False)
```

For example, say you have a personal directory on mdss:
```
mdss ls -ld personal/me
drwxrws--- 4 abc123 x77 92 Dec 14  2014 personal/me
```
And you have used mdss to put another directory there
```
mdss put -r data personal/me/
mdss ls -ld personal/me/data
-rw-r--r-- 1 abc123 a00  1219 Nov  9 12:40 personal/me/data
```
To check if all the files have been correctly copied:
```
mdssdiff -p personal/me -r data
```
This will show a list of which files are present/absent on the local or remote (mdss) filesystem. It 
will also notify show any files which differ in size.
