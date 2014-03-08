#!/usr/local/bin/python

"""
Move files matching a Unix shell-style wildcard expression between directories.
Useful when too many files for shell argument expansion.
"""

from optparse import OptionParser
import os
import sys
from fnmatch import fnmatch

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <pattern> <dir1> <dir2>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    pattern = args[0]
    dir1 = args[1]
    dir2 = args[2]
    if not os.path.isdir(dir1):
        print >> sys.stderr, 'Cannot find dir: %s' % dir1
        return
    if not os.path.isdir(dir2):
        print >> sys.stderr, 'Cannot find dir: %s' % dir2
        return

    count = 0
    for filename in os.listdir(dir1):
        if not fnmatch(filename, pattern):
            continue
        os.rename(os.path.join(dir1, filename), os.path.join(dir2, filename))
        count += 1

    print 'Moved %d files from %s to %s' % (count, dir1, dir2)

if __name__ == '__main__':
    main()
