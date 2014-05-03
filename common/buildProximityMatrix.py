#!/usr/bin/env python

"""
Performs a breadth-first-search starting from each node to construct a
matrix of proximities/closeness from each node i to each node j.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import math
import sqlite3
from collections import deque
from random import shuffle

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
        help='Category to confine walks to.', metavar='CAT')
    parser.add_option('--decay', type='float', dest='decay', default=1.0,
        help='Decay constant applied to proximity values.', metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile', default='proxMatrix.npz',
        help='Save file name for proximity matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildProximityMatrix(graph, nodes, decay=1.0):
    assert(len(nodes) == len(set(nodes)))
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    proxMatrix = np.zeros((len(nodes), len(nodes)))
    shuffle(nodes)
    for source in nodes:
        visited = set()
        q = deque()
        q.appendleft((source, 0))
        while q:
            (n, x) = q.pop()
            if n in visited: continue
            visited.add(n)
            assert(proxMatrix[node2id[source],node2id[n]] == 0.0)
            proxMatrix[node2id[source],node2id[n]] = math.exp(-decay*x)
            shuffle(graph[n][0])
            for neighbor in graph[n][0]:
                if neighbor in visited: continue
                q.appendleft((neighbor, x+1))
    return proxMatrix

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % graphfname
        return

    # load graph
    graph = loadGraph(graphfname)

    # get category items if category provided
    if options.category is not None:
        if options.dbname is None:
            print >> sys.stderr,\
                'ERROR: Must provide --database if --category provided'
            return
        print 'Connecting to %s. . .' % options.dbname
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
        print 'Reading category products. . .'
        db_curs.execute(selectCategoryProductsStmt, (options.category,))
        dictionary = [row[0] for row in db_curs.fetchall() if row[0] in graph]
        print 'Retrieved %d category products.' % len(dictionary)
    else:
        dictionary = graph.keys()

    # build proximity matrix
    print 'Building proximity matrix. . .'
    proxMatrix = buildProximityMatrix(graph, dictionary, decay=options.decay)

    # save proximity Matrix
    print 'Saving proximity matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=proxMatrix, dictionary=dictionary)

if __name__ == '__main__':
    main()
