#!/usr/bin/env python

"""
Identify all nodes in a directed graph that are part of a 5 node or fewer trap,
where a trap is defined as a subgraph from which there are no outgoing edges.
"""

from optparse import OptionParser
import pickle
import os
import sys
import sqlite3

# local modules
from Graph_util import loadGraph

# db params
selectCategoryProductsStmt =\
    ('SELECT Id '
     'FROM Categories '
     'WHERE Category = :Category')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--category', dest='category', default=None,
        help='Category to confine start of random walks.', metavar='CAT')
    return parser

def findTrapNodes(graph, nodes):
    trapNodes = []
    examined = {}
    for node in nodes:
        if node in trapNodes: continue
        foundExit = False
        for neighbor in graph[node][0]:
            if neighbor not in nodes: continue
            for secondNeighbor in graph[neighbor][0]:
                if secondNeighbor not in nodes: continue
                if secondNeighbor != node and\
                   secondNeighbor not in graph[node][0]:
                    foundExit = True
                    break
            if foundExit: break
        if not foundExit:
            trapNodes.append(node)
            trapNodes += graph[node][0]
    return trapNodes

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
    graph = loadGraph(graphfname)

    # get category items if category provided
    if options.category is not None:
        if options.dbname is None:
            parser.error('Must provide --database if --category provided')
        print 'Connecting to %s. . .' % options.dbname
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
        print 'Reading category products. . .'
        db_curs.execute(selectCategoryProductsStmt, (options.category,))
        nodes = [row[0] for row in db_curs.fetchall() if row[0] in graph]
        print 'Retrieved %d category products.' % len(nodes)
    else:
        nodes = graph.keys()

    # find traps
    trapNodes = findTrapNodes(graph, nodes)

    # display traps
    print trapNodes
    print 'Found %d nodes that participate in traps.' % len(trapNodes)

if __name__ == '__main__':
    main()
