#!/usr/local/bin/python

"""
Removes repeated lines while also requiring minimum number of repeats to qualify
for inclusion in output.
"""

from optparse import OptionParser
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--minRepeats', dest='minRepeats', type='int',
        default=1,
        help='Minimum number of consecutive repeats for inclusion of line.',
        metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <file>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return

    lastLine = None
    repeats = 0
    inputfile = open(inputfilename, 'r')
    for line in inputfile:
        #print 'repeats = %d' % repeats
        #print 'Read:', line
        if line == lastLine:
            repeats += 1
            continue
        if repeats >= options.minRepeats:
            #print 'Write:', lastLine
            print lastLine.rstrip()
        lastLine = line
        repeats = 1
    if repeats >= options.minRepeats:
        print lastLine

if __name__ == '__main__':
    main()
