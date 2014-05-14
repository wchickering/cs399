#!/usr/bin/env python

"""
Test the partition from partitionGraph.py.
"""

from stemming.porter2 import stem
from optparse import OptionParser
from collections import deque
import pickle
import random
import os
import sys
import string
import sqlite3

selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'

def getParser():
    parser = OptionParser()
    parser.add_option('-g', '--graph', dest='graphfilename',
        help='Name of picked directed graph.', metavar='FILE')
    parser.add_option('--graph1', dest='graph1filename',
        help='Name of partitioned graph1 pickle.', metavar='FILE')
    parser.add_option('--graph2', dest='graph2filename',
        help='Name of partitioned graph2 pickle.', metavar='FILE')
    parser.add_option('--lost_edges', dest='lostedgesfilename',
        help='Name of lost edges pickle.', metavar='FILE')
    parser.add_option('-s', '--sample_percent', dest='sample_percent',
        default='1.0',
        help='Percent of nodes/edges to check', metavar='NUM')
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Database to pull descriptions from.')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def constructItemMap(graph1, graph2):
    print 'Check that no node is in both graphs. .'
    itemMap = {}
    for item in graph1:
        if item in itemMap:
            print 'Fail ==> item %s in partitioned graphs twice' % item
        itemMap[item] = 1
    for item in graph2:
        if item in itemMap:
            print 'Fail ==> item %s in partitioned graphs twice' % item
        itemMap[item] = 2
    return itemMap

def testNodePartition(graph, graph1, graph2, itemMap):
    print ' Graph size: %d' % len(graph)
    print ' Graph1 size: %d' % len(graph1)
    print ' Graph2 size: %d' % len(graph2)
    if len(graph) != len(graph1) + len(graph2):
        print 'FAIL ==> Graph size != graph1 size + graph2 size'
    for item in graph:
        if itemMap[item] == None:
            print 'FAIL ==> node %s not in either graph' % node
    return

def testLostedges(db_conn, lost_edges, graph, itemMap):
    print ' Numnber of lost edges: %d' % len(lost_edges)
    db_curs = db_conn.cursor()
    outOf1 = 0
    for (item1, item2) in lost_edges:
        if itemMap[item1] == 1:
            outOf1 += 1
        if itemMap[item1] == itemMap[item2]:
            print 'FAIL ==> lost_edge (%s, %s) has both nodes in same graph' %\
                (item1, item2)
            return
        # get brands
        db_curs.execute(selectDescriptionStmt, (item1,))
        description = db_curs.fetchone()[0]
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        words = [stem(w.lower()) for w in description.split()]
        brand1 = words[0]
        db_curs.execute(selectDescriptionStmt, (item2,))
        description = db_curs.fetchone()[0]
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        words = [stem(w.lower()) for w in description.split()]
        brand2 = words[0]
        if brand1 == brand2:
            print 'FAIL ==> same brand in both graphs'
    print ' Number of edges out of graph1: %d' % outOf1
    print ' Number of edges out of graph2: %d' % (len(lost_edges) - outOf1)
    print ' Lost edges per node: %f' % (float(len(lost_edges)) / (len(graph)))
    return

def testGraph(graph, graphNum, itemMap):
    for item in graph:
        (outbound, inbound) = graph[item]
        for out_item in outbound:
            if itemMap[out_item] != graphNum:
                print 'FAIL ==> outbound item %s not in graph %d' % (out_item,
                    graphNum)
                return
        for in_item in outbound:
            if itemMap[in_item] != graphNum:
                print 'FAIL ==> inbound item %s not in graph %d' % (in_item,
                    graphNum)
                return
    return

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

    # connect to database
    print 'Connecting to database. .'
    db_conn = sqlite3.connect(options.dbname)

    # construct item map
    print 'Constructing item map and checking nodes are only in one graph. . .'
    itemMap = constructItemMap(graph1, graph2)

    # test graph
    print 'Check that nodes in graph are partitioned. . .'
    testNodePartition(graph, graph1, graph2, itemMap)

    print 'Check that lost_edges are between two graphs. . .'
    testLostedges(db_conn, lost_edges, graph, itemMap)

    print 'Check that edges of partitioned graphs are valid. . .'
    testGraph(graph1, 1, itemMap)
    testGraph(graph2, 2, itemMap)

if __name__ == '__main__':
    main()
