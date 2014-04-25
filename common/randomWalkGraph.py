#!/usr/bin/env python

"""
Performs a random walk on a directed graph to yield a matrix of probabilities
that a walker starting at node i ends up at node j after k steps.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import sqlite3

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
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of steps in random walk.', metavar='NUM')
    parser.add_option('-t', '--teleport', type='float', dest='teleport',
        default=0.0, help='Weight of additional "teleportation" edge.',
        metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile',
        default='data/walkMatrix.npz',
        help='Save file name for random walk matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildTransitionMatrix(graph, nodes, teleport):
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    tranMatrix = np.zeros((len(nodes), len(nodes)))
    for node in nodes:
        neighbors = [neighbor for neighbor in graph[node][0]\
                     if neighbor in node2id]
        neighbors.append(node) # self loop
        normalization = len(neighbors) + teleport
        tranMatrix[node2id[node],:] = teleport/(normalization*len(nodes));
        p = 1.0/normalization
        for neighbor in neighbors:
            tranMatrix[node2id[node], node2id[neighbor]] += p
    return tranMatrix, node2id

def randomWalk(tranMatrix, k):
    assert(tranMatrix.shape[0] == tranMatrix.shape[1])
    walkMatrix = np.identity(tranMatrix.shape[0])
    for i in range(k):
        walkMatrix = np.dot(tranMatrix, walkMatrix)
    return walkMatrix

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
        nodes = [row[0] for row in db_curs.fetchall() if row[0] in graph]
        print 'Retrieved %d category products.' % len(nodes)
    else:
        nodes = graph.keys()

    # create transition matrix
    print 'Building transition matrix. . .'
    tranMatrix, item2id = buildTransitionMatrix(graph, nodes, options.teleport)

    # do random walk
    print 'Performing %d step random walk. . .' % options.k
    walkMatrix = randomWalk(tranMatrix, options.k)

    # write walkMatrix nodes to disk
    print 'Saving walk matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=walkMatrix, nodes=nodes)

    # debugging
    #print 'Do debugging. . .'
    #item = 1246874
    #topn = 10
    #destinations =\
    #    [(ind, prob) for ind, prob in enumerate(walkMatrix[item2id[item],:])]
    #destinations = sorted(destinations, key=lambda x: x[1], reverse=True)
    #print 'dest: prob for %d (top %d)' % (item, topn)
    #for i in range(topn):
    #    print '%d: %f' % (nodes[destinations[i][0]], destinations[i][1])

    # TODO: write walkMatrix to disk and/or construct a new graph from
    # walkMatrix.

if __name__ == '__main__':
    main()
