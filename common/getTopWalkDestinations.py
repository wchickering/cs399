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

# local modules
from SessionTranslator import SessionTranslator

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of destinations to display.', metavar='NUM')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def getDestinations(item, matrix, dictionary):
    itemId = -1
    for i in range(len(dictionary)):
        if dictionary[i] == item:
            itemId = i
            break
    if itemId == -1:
        print >> sys.stderr, 'ERROR: Failed to find item in dictionary.'
        return None
    destinations =\
        [(dictionary[ind], prob) for ind, prob in enumerate(matrix[itemId,:])]
    return sorted(destinations, key=lambda x: x[1], reverse=True)

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
    item = int(args[1])

    # load matrix
    print 'Loading matrix from %s. . .' % matrixfname
    npzfile = np.load(matrixfname)
    matrix = npzfile['matrix']
    dictionary = npzfile['dictionary']

    # get translator
    if options.dbname is not None:
        translator = SessionTranslator(options.dbname)
    else:
        translator = None

    # get destinations
    destinations = getDestinations(item, matrix, dictionary)

    # display top N destinations
    name = None
    if translator is not None:
        description = translator.sessionToDesc([item])[0]
        name = '(%d) %s' % (item, description)
    if name is None:
        name = '%d' % item
    print 'dest: prob for %s (top %d)' % (name, options.topn)
    for i in range(options.topn):
        neighbor = destinations[i][0]
        distance = destinations[i][1]
        name = None
        if translator is not None:
            description = translator.sessionToDesc([neighbor])[0]
            name = '(%d) %s' % (neighbor, description)
        if name is None:
            name = '%d' % neighbor
        print '%s: %.2e' % (name, distance)

if __name__ == '__main__':
    main()
