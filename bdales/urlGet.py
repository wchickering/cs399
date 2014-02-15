#!/usr/local/bin/python

import sys
import os
import urllib2
from optparse import OptionParser

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--output', dest='outfilename', default=None,
        help='Output file.', metavar='OUT_FILE')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] url'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    url = args[0]
    if options.outfilename:
        assert(os.path.isfile(options.outfilename))
        outfile = open(options.outfilename, 'w')
    else:
        outfile = sys.stdout

    # Attempt to open url
    try:
        html = urllib2.urlopen(url).read()
    except ValueError:
        print >> sys.stderr, 'Failed to open url: %s' % url
        return

    outfile.write(html)
    outfile.close()

if __name__ == '__main__':
    main()
