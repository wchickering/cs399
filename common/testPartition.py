#!/usr/bin/env python

"""
Test the partition from partitionGraph.py
"""

from optparse import OptionParser
from collections import deque
import pickle
import random
import os
import sys

# params
displayInterval = 100

def getParser():
    parser = OptionParser()
    parser.add_option('-g', '--graph', dest='graphfilename',
        default='data/recDirectedGraph.pickle',
        help='Name of picked directed graph.', metavar='FILE')
    parser.add_option('--graph1', dest='graph1filename',
        default='data/partitionedGraph1.pickle',
        help='Name of partitioned graph1 pickle.', metavar='FILE')
    parser.add_option('--graph2', dest='graph2filename',
        default='data/partitionedGraph2.pickle',
        help='Name of partitioned graph2 pickle.', metavar='FILE')
    parser.add_option('--lost_edges', dest='lostedgesfilename',
        default='data/lostEdges.pickle',
        help='Name of lost edges pickle.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # load recommendation graph
    graph = loadGraph(options.graphfilename)
    graph1 = loadGraph(options.graph1filename)
    graph2 = loadGraph(options.graph2filename)
    edges = loadGraph(options.lostedgesfilename)

    # test graph
    print 'Make sure nodes of graph are partitioned into graph1 and graph2. .'
    count = 0
    for node in graph.keys():
        count += 1
        if count % displayInterval == 0:
            print 'Processing node %d' % count
        (outbound, inbound) = graph[node]
        if node not in graph1.keys() and node not in graph2.keys():
            print 'FAIL ==> node %s not in either graph' % node
        if node in graph1.keys() and node in graph2.keys():
            print 'FAIL ==> node %s in both graph1 and graph2' % node
        if node in graph1.keys():
            (outbound1, inbound1) = graph1[node]
            for v in outbound1:
                if v not in outbound:
                    print 'FAIL ==> edge in outbound1[%s] not in outbound[%s]'
        if node in graph2.keys():
            (outbound2, inbound2) = graph2[node]
            for v in outbound2:
                if v not in outbound:
                    print 'FAIL ==> edge in outbound2[%s] not in outbound[%s]'

if __name__ == '__main__':
    main()
