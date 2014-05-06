#!/usr/bin/env python

"""
Partitions a graph into two graphs, each with half of the nodes and no edges
between them. Stores both partitioned graphs and the lost edges from the
partition.
"""

from optparse import OptionParser
import pickle
import random
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--graph1', dest='graph1filename',
        default='partitionedGraph1.pickle',
        help='Name of partitioned graph1 pickle.', metavar='FILE')
    parser.add_option('--graph2', dest='graph2filename',
        default='partitionedGraph2.pickle',
        help='Name of partitioned graph2 pickle.', metavar='FILE')
    parser.add_option('--lost_edges', dest='lostedgesfilename',
        default='lostEdges.pickle', help='Name of lost edges pickle.',
        metavar='FILE')
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
    usage = 'Usage: %prog [options] graph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        parser.error('Cannot find %s' % graphfname)

    # load graph
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    # seed rng
    random.seed(options.seed)

    # partition graph
    print 'Partitioning graph. . .'
    results = partitionGraph(graph)
    graph1 = results[0]
    graph2 = results[1]
    lost_edges = results[2]
    
    # dump results
    print 'Saving graph1 to %s. . .' % options.graph1filename
    pickle.dump(graph1, open(options.graph1filename, 'w'))
    print 'Saving graph2 to %s. . .' % options.graph2filename
    pickle.dump(graph2, open(options.graph2filename, 'w'))
    print 'Saving lost edges to %s. . .' % options.lostedgesfilename
    pickle.dump(lost_edges, open(options.lostedgesfilename, 'w'))

if __name__ == '__main__':
    main()
