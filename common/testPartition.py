#!/usr/bin/env python

"""
Test the partition from partitionGraph.py.
"""

from optparse import OptionParser
from collections import deque
import pickle
import random
import os
import sys

# params
displayInterval = 1000000

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
    parser.add_option('-s', '--sample_percent', dest='sample_percent',
        default='1.0',
        help='Percent of nodes/edges to check', metavar='NUM')
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
    print 'Load pickles. .'
    graph = loadGraph(options.graphfilename)
    graph1 = loadGraph(options.graph1filename)
    graph2 = loadGraph(options.graph2filename)
    lost_edges = loadGraph(options.lostedgesfilename)

    # construct item map
    print 'Check that no node is in both graphs. .'
    itemMap = {}
    count = 0
    for item in graph1.keys():
        count += 1
        if count % displayInterval == 0:
            print 'Processing node %d / %d' % (count, len(graph1.keys()))
        if item in itemMap:
            print 'Fail ==> item %s in partitioned graphs twice' % item
        itemMap[item] = 1
    count = 0
    for item in graph2.keys():
        count += 1
        if count % displayInterval == 0:
            print 'Processing node %d / %d' % (count, len(graph2.keys()))
        if item in itemMap:
            print 'Fail ==> item %s in partitioned graphs twice' % item
        itemMap[item] = 2

    # test graph
    print 'Check that nodes in graph are partitioned. .'
    if len(graph.keys()) != len(graph1.keys()) + len(graph2.keys()):
        print 'FAIL ==> Graph size != graph1 size + graph2 size'
    count = 0
    for item in graph:
        count += 1
        if count % displayInterval == 0:
            print 'Processing node %d / %d' % (count, len(graph.keys()))
        if random.random() > float(options.sample_percent):
            continue
        if itemMap[item] == None:
            print 'FAIL ==> node %s not in either graph' % node

    print 'Check that lost_edges are between two graphs. .'
    count = 0
    for (item1, item2) in lost_edges:
        count += 1
        if count % displayInterval == 0:
            print 'Processing edge %d / %d' % (count, len(lost_edges))
        if random.random() > float(options.sample_percent):
            continue
        if itemMap[item1] == itemMap[item2]:
            print 'FAIL ==> lost_edge (%s, %s) has both nodes in same graph' %\
                (node1, node2)

    print 'Check that edges of graph1 are within graph1. .'
    count = 0
    for item in graph1:
        count += 1
        if count % displayInterval == 0:
            print 'Processing edge %d / %d' % (count, len(graph1))
        if random.random() > float(options.sample_percent):
            continue
        (outbound, inbound) = graph1[item]
        for out_item in outbound:
            if itemMap[out_item] != 1:
                print 'FAIL ==> outbound item %s not in graph 1' % out_item
        for in_item in outbound:
            if itemMap[in_item] != 1:
                print 'FAIL ==> inbound item %s not in graph 1' % in_item

    print 'Check that edges of graph2 are within graph2. .'
    count = 0
    for item in graph2:
        count += 1
        if count % displayInterval == 0:
            print 'Processing edge %d / %d' % (count, len(graph2))
        if random.random() > float(options.sample_percent):
            continue
        (outbound, inbound) = graph2[item]
        for out_item in outbound:
            if itemMap[out_item] != 2:
                print 'FAIL ==> outbound item %s not in graph 2' % out_item
        for in_item in outbound:
            if itemMap[in_item] != 2:
                print 'FAIL ==> inbound item %s not in graph 2' % in_item

if __name__ == '__main__':
    main()
