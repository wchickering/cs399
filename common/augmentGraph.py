#!/usr/bin/env python

"""
Augments a graph by adding nodes and/or edges.
"""

from optparse import OptionParser
import os
import sys

#local modules
from Util import loadPickle
from Graph_util import GraphError, loadGraph, saveGraph, addNodes, addEdges,\
                       mergeGraphs

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--nodes', dest='nodes', default=None,
        help='Pickled list representing new nodes.', metavar='FILE')
    parser.add_option('--edges', dest='edges', default=None,
        help='Pickled list of tuples representing new edges.', metavar='FILE')
    parser.add_option('--savefile', dest='savefile',
        default='augmentedGraph.pickle', help='Save file for augmented graph.',
        metavar='FILE')
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

    # add new nodes
    if options.nodes is not None:
        if not os.path.isfile(options.nodes):
            parser.error('Cannot find %s' % options.nodes)
        nodes = loadPickle(options.nodes)
        try:
            addNodes(graph, nodes)
        except GraphError as e:
            print >> sys.stderr, e.message
            return

    # add new edges
    if options.edges is not None:
        if not os.path.isfile(options.edges):
            parser.error('Cannot find %s' % options.edges)
        edges = loadPickle(options.edges)
        try:
            addEdges(graph, edges)
        except GraphError as e:
            print >> sys.stderr, e.message
            return

    # save graph
    print 'Saving modified graph to %s. . .' % options.savefile
    saveGraph(graph, options.savefile)

if __name__ == '__main__':
    main()

