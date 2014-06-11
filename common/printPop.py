#!/usr/bin/env python

"""
Prints the degrees of each node
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
    print 'Printing popularities. . .'
    for item in graph:
        print len(graph[item][1])

if __name__ == '__main__':
    main()
