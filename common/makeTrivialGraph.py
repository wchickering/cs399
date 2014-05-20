#!/usr/bin/env python

from optparse import OptionParser
import pickle
import os
import sys

# local modules
from Graph_util import saveGraph

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--output', dest='outfilename',
        default='trivialGraph.pickle',
        help='Output pickle file containing trivial graph.',
        metavar='FILE')
    return parser

def makeTrivialGraph():
    graph = {}
    # nodes
    graph[42] = ([], [])
    graph[100] = ([], [])
    graph[6] = ([], [])
    # edges
    graph[42][0].append(100)
    graph[42][0].append(6)
    graph[42][1].append(6)
    graph[100][0].append(6)
    graph[100][1].append(42)
    graph[6][0].append(42)
    graph[6][1].append(42)
    graph[6][1].append(100)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # make trivial graph
    print 'Making trivial graph. . .'
    graph = makeTrivialGraph()

    # save graph
    print 'Saving graph to %s. . .' % options.outfilename
    saveGraph(graph, options.outfilename)

if __name__ == '__main__':
    main()
