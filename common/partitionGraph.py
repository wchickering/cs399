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
    # partition nodes, keeping all edges
    count = 0
    print 'Shuffling graph'
    random.shuffle(graph.keys())
    print 'Partitioning nodes'
    nodes_per_graph = len(graph.keys())/2
    for item in graph.keys():
        count += 1
        if count < nodes_per_graph:
            graph1[item] = graph[item]
        else:
            graph2[item] = graph[item]
    # remove edges across graphs and save them
    print 'Removing edges from paritioned graphs'
    lost_edges = []
    items = 0
    for item in graph1.keys():
        if items % displayInterval == 0:
            print 'Proceseed %d items' % items
        items += 1
        (outbound, inbound) = graph1[item]
        # remove graph2 nodes from outbound and add to lost_edges
        for node in outbound:
            if node in graph2.keys():
                lost_edges.append((item, node))
                graph1[item][0].remove(node)
                graph2[node][1].remove(item)
        # remove graph2 nodes from inbound and add to lost_edges
        for node in inbound:
            if node in graph2.keys():
                lost_edges.append((node, item))
                graph1[item][1].remove(node)
                graph2[node][0].remove(item)
    return (graph1, graph2, lost_edges)

def main():
    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # seed rng
    random.seed(options.seed)

    # load recommendation graph
    graph = loadGraph(options.graphfilename)

    # partition graph
    results = partitionGraph(graph)
    graph1 = results[0]
    graph2 = results[1]
    lost_edges = results[2]
    
    # dump results
    pickle.dump(graph1, open(options.graph1filename, 'w'))
    pickle.dump(graph2, open(options.graph2filename, 'w'))
    pickle.dump(lost_edges, open(options.lostedgesfilename, 'w'))

if __name__ == '__main__':
    main()
