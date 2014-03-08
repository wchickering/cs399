#!/usr/local/bin/python

"""
Count files in a directory matching a Unix shell-style wildcard expression.
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
    usage = 'Usage: %prog [options] <pattern> <dir>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    pattern = args[0]
    directory = args[1]
    if not os.path.isdir(directory):
        print >> sys.stderr, 'Cannot find: %s' % directory
        return

    count = 0
    for filename in os.listdir(directory):
        if not fnmatch(filename, pattern):
            continue
        count += 1

    print count

if __name__ == '__main__':
    main()
