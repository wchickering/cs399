#!/usr/bin/env python

"""
Renames files by changes prefix and/or suffix.
"""

from optparse import OptionParser
import os
import sys
from fnmatch import fnmatch

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--prefix1', dest='prefix1', default=None,
        help='Prefix of original filenames.', metavar='STR')
    parser.add_option('--prefix2', dest='prefix2', default=None,
        help='Prefix of new filenames.', metavar='STR')
    parser.add_option('--suffix1', dest='suffix1', default=None,
        help='Suffix of original filenames.', metavar='STR')
    parser.add_option('--suffix2', dest='suffix2', default=None,
        help='Suffix of new filenames.', metavar='STR')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] dir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    directory = args[0]
    if not os.path.isdir(directory):
        print >> sys.stderr, 'Cannot find dir: %s' % directory
        return

    count = 0
    for filename in os.listdir(directory):
        if options.prefix1 and not filename.startswith(options.prefix1):
            continue
        if options.suffix1 and not filename.endswith(options.suffix1):
            continue
        # determine new filename
        newname = filename
        if options.prefix1:
            newname = newname[len(options.prefix1):]
        if options.suffix1:
            newname = newname[0:-len(options.suffix1)]
        if options.prefix2:
            newname = options.prefix2 + newname 
        if options.suffix2:
            newname = newname + options.suffix2
            
        os.rename(os.path.join(directory, filename), os.path.join(directory, newname))
        count += 1

    print 'Renamed %d files.' % count

if __name__ == '__main__':
    main()
