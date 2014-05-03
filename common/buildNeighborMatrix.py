#!/usr/bin/env python

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import math
import sqlite3
from collections import deque

# params
epsilon = 0.1

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
    parser.add_option('--savefile', dest='savefile',
        default='neighborMatrix.npz',
        help='Save file name for neighbor matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildNeighborMatrix(graph, nodes):
    assert(len(nodes) == len(set(nodes)))
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    neighborMatrix = np.identity(len(nodes))
    for source in nodes:
        for neighbor in graph[source][0]:
            neighborMatrix[node2id[source],node2id[neighbor]] =\
                1.0/len(graph[source][0]) - epsilon
    return neighborMatrix

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

    # build neighbor matrix
    print 'Building neighbor matrix. . .'
    neighborMatrix = buildNeighborMatrix(graph, dictionary)

    # save neighbor matrix
    print 'Saving neighbor matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=neighborMatrix, dictionary=dictionary)

if __name__ == '__main__':
    main()
