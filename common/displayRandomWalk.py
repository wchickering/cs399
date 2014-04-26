#!/usr/bin/env python

"""
Displays the most probable destinations for a random walk that began at a
partiular node.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of destinations to display.', metavar='NUM')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] <randomWalk.npz> <item>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    matrixfname = args[0]
    if not os.path.isfile(matrixfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % matrixfname
        return
    item = args[1]

    # load matrix
    print 'Loading matrix from %s. . .' % matrixfname
    npzfile = np.load(matrixfname)
    matrix = npzfile['matrix']
    dictionary = npzfile['dictionary']

    itemId = -1
    for i in range(len(dictionary)):
        if str(dictionary[i]) == item:
            itemId = i
            break
    if itemId == -1:
        print >> sys.stderr, 'ERROR: Failed to find item in dictionary.'
        return
    destinations =\
        [(ind, prob) for ind, prob in enumerate(matrix[itemId,:])]
    destinations = sorted(destinations, key=lambda x: x[1], reverse=True)
    print 'dest: prob for %s (top %d)' % (item, options.topn)
    for i in range(options.topn):
        print '%d: %f' % (dictionary[destinations[i][0]], destinations[i][1])

if __name__ == '__main__':
    main()
