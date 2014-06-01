#!/usr/bin/env python

"""
Constructs dictionary of item "popularity", defined as the natural logarithm of
the item's in-degree within its associated recommendation graph.
"""

from optparse import OptionParser
import os
import sys
import pickle
import math

#local modules
from Util import loadPickle
from Graph_util import loadGraph, mergeGraphs

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--alpha', type='float', dest='alpha', default=1.0,
        help='Scaling parameter for popularity.', metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile',
        default='popDictionary.pickle',
        help='Save file for popularity dictionary.', metavar='FILE')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] [graph1.pickle] [graph2.pickle] ...'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # read and merge graphs
    graph = {}
    for i in range(len(args)):
        graphfname = args[i]
        if not os.path.isfile(graphfname):
            parser.error('Cannot find %s' % graphfname)
        # load graph
        print 'Loading graph from %s. . .' % graphfname
        g = loadGraph(graphfname)
        graph = mergeGraphs(graph, g)

    # build pop dictionary
    print 'Building popularity dictionary. . .'
    popDictionary = {}
    for item in graph:
        popDictionary[item] = math.log(1.0 + len(graph[item][1])/options.alpha)

    # save pop dictionary
    print 'Saving popularity dictionary to %s. . .' % options.savefile
    pickle.dump(popDictionary, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
