# mdssdiff
Look for differences between local filesystem and it's copy on a mass data store system

```
usage: mdssdiff.py [-h] [-v] [-p PATHPREFIX] [-r] inputs [inputs ...]

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
