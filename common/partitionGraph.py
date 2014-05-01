#!/usr/bin/env python

"""
Partitions a graph into two graphs, each with half of the nodes and no edges
between them. Stores both partitioned graphs and the lost edges from the
partition.
"""

from optparse import OptionParser
from collections import deque
import pickle
import random
import os
import sys

# params
displayInterval = 1000

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
    parser.add_option('--seed', type='int', dest='seed', default=0,
        help='Seed for random number generator.', metavar='NUM')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def partitionGraph(graph):
    graph1 = {}
    graph2 = {}
    itemMap = {}
    # partition nodes, keeping all edges
    count = 0
    random.shuffle(graph.keys())
    nodes_per_graph = len(graph.keys())/2
    for item in graph.keys():
        count += 1
        if count < nodes_per_graph:
            itemMap[item] = 1
        else:
            itemMap[item] = 2
    # remove edges across graphs and save them
    lost_edges = []
    for item in graph.keys():
        (outbounds, inbounds) = graph[item]
        newOutbounds = []
        newInbounds = []
        # only add inbound/outbound edges if nodes are in same the graph
        for outbound in outbounds:
            if itemMap[outbound] == itemMap[item]:
                newOutbounds.append(outbound)
            else:
                lost_edges.append((item, outbound))
        for inbound in inbounds:
            if itemMap[inbound] == itemMap[item]:
                newInbounds.append(inbound)
            else:
                lost_edges.append((item, inbound))
        # add to appropriate graph
        if itemMap[item] == 1:
            graph1[item] = (newOutbounds, newInbounds)
        else:
            graph2[item] = (newOutbounds, newInbounds)
    return (graph1, graph2, lost_edges)

def main():
    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # seed rng
    random.seed(options.seed)

    print 'Load graph. .'
    # load recommendation graph
    graph = loadGraph(options.graphfilename)

    print 'Partition graph. .'
    # partition graph
    results = partitionGraph(graph)
    graph1 = results[0]
    graph2 = results[1]
    lost_edges = results[2]
    
    print 'Dump results. .'
    # dump results
    pickle.dump(graph1, open(options.graph1filename, 'w'))
    pickle.dump(graph2, open(options.graph2filename, 'w'))
    pickle.dump(lost_edges, open(options.lostedgesfilename, 'w'))

if __name__ == '__main__':
    main()
