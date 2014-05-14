#!/usr/bin/env python

"""
Partitions a graph into two graphs, each with half of the nodes and no edges
between them. Stores both partitioned graphs and the lost edges from the
partition.
"""

from stemming.porter2 import stem
from optparse import OptionParser
import pickle
import random
import string
import os
import sys
import sqlite3

selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'

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
    parser.add_option('--seed', type='int', dest='seed', default=10,
        help='Seed for random number generator.', metavar='NUM')
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Database to pull descriptions from.')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def partitionNodesByBrand(db_conn, graph):
    db_curs = db_conn.cursor()
    itemMap = {}
    brandMap = {}
    for item in graph:
        db_curs.execute(selectDescriptionStmt, (item,))
        description = db_curs.fetchone()[0]
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        words = [stem(w.lower()) for w in description.split()]
        brand = words[0]
        if brand not in brandMap:
            brandMap[brand] = random.choice([1,2])
        itemMap[item] = brandMap[brand]
    count = 0 
    for brand in brandMap:
        count += 1
        print brand
    print 'Number of brands = %d' % count
    return itemMap

def buildGraphs(itemMap, graph):
    lost_edges = []
    graph1 = {}
    graph2 = {}
    for item in graph:
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

    # connect to database
    print 'Connecting to database. .'
    db_conn = sqlite3.connect(options.dbname)

    # partition graph
    print 'Partitioning graph. . .'
    itemMap = partitionNodesByBrand(db_conn, graph)
    results = buildGraphs(itemMap, graph)
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
