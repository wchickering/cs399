#!/usr/bin/env python

"""
Removes one or more specified nodes from a graph.
"""

from optparse import OptionParser
import os
import sys

# local modules
from Graph_util import loadGraph, saveGraph, extractNodes

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile',
        default='modifiedGraph.pickle', help='Save file for modified graph.',
        metavar='FILE')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph.pickle node1 [node2] [node3] [...]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        parser.error('Cannot find %s' % graphfname)

    # load graph
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    # parse nodes
    nodes = []
    for i in range(1, len(args)):
        try:
            node = int(args[i])
        except:
            parser.error('Invalid node value: %s' % args[i])
        nodes.append(node)

    # extract nodes
    extractNodes(graph, nodes)

    # save graph
    print 'Saving modified graph to %s. . .' % options.savefile
    saveGraph(graph, options.savefile)

if __name__ == '__main__':
    main()
