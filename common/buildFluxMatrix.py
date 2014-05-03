#!/usr/bin/env python

"""
Performs a breadth-first-search starting from each node to construct a
matrix of "flux" from each node i to each node j.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import math
import sqlite3
from collections import deque

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
    parser.add_option('--epsilon', type='float', dest='epsilon', default=0.1,
        help='Espilon parameter for flux algorithm.', metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile', default='fluxMatrix.npz',
        help='Save file name for flux matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildFluxMatrix(graph, nodes, epsilon=0.1):
    assert(len(nodes) == len(set(nodes)))
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    fluxMatrix = np.zeros((len(nodes), len(nodes)))
    for source in nodes:
        visited = set()
        q = deque()
        q.appendleft((source, 1.0))
        while q:
            (n, x) = q.pop()
            if n in visited: continue
            visited.add(n)
            assert(fluxMatrix[node2id[source],node2id[n]] == 0.0)
            fluxMatrix[node2id[source],node2id[n]] = (1.0 - epsilon)*x
            for neighbor in graph[n][0]:
                if neighbor in visited: continue
                q.appendleft((neighbor, x/len(graph[n][0])))
    return fluxMatrix

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

    # build flux matrix
    print 'Building flux matrix. . .'
    fluxMatrix = buildFluxMatrix(graph, dictionary, epsilon=options.epsilon)

    # save proximity Matrix
    print 'Saving flux matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=fluxMatrix, dictionary=dictionary)

if __name__ == '__main__':
    main()
