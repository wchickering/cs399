#!/usr/bin/env python

"""
Delete all files in a directory that have fewer than n lines.
"""

from optparse import OptionParser
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def linesLessThan(n, fullpath):
    count = 0
    with open(fullpath, 'r') as f:
        for i, l in enumerate(f):
            if i + 1 >= n:
                return False
    return True

def main():
    # Parse options
    usage = 'Usage: %prog [options] N <dir>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    try:
        n = int(args[0])
    except ValueError:
        print >> sys.stderr, 'Invalid number of lines: %s' % args[0]
        return
    if not os.path.isdir(args[1]):
        print >> sys.stderr, 'Cannot find directory: %s' % args[1]
        return
    inputDir = args[1]

    num_removes = 0
    for filename in os.listdir(inputDir):
        fullpath = os.path.join(inputDir, filename)
        if not os.path.isfile(fullpath):
            continue
        if linesLessThan(n, fullpath):
            os.remove(fullpath)
            num_removes += 1
    print 'Removed %d files.' % num_removes

if __name__ == '__main__':
    main()
