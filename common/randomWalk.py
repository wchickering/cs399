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
    parser.add_option('--teleport', type='float', dest='teleport',
        default=0.0, help='Weight of additional "teleportation" edge.',
        metavar='FLOAT')
    parser.add_option('--home', type='float', dest='home', default=0.0,
        help='Probability of teleporting back to starting node.',
        metavar='FLOAT')
    parser.add_option('--reverse', action='store_true', dest='reverse',
        default=False, help='Follow incoming edges.')
    parser.add_option('--savefile', dest='savefile',
        default='data/randomWalk.npz',
        help='Save file name for random walk matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

# Experimental transition matrix that decreases likelihood of transitioning to
# nodes with many incoming edges.
def buildTransitionMatrix2(graph, nodes, teleport=0.0, reverse=False):
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    tranMatrix = np.zeros((len(nodes), len(nodes)))
    for node in nodes:
        neighbors = [neighbor for neighbor in graph[node][1 if reverse else 0]\
                     if neighbor in node2id]
        weights = [0.0]*len(neighbors)
        for i in range(len(neighbors)):
            weights[i] = 1.0/len(graph[neighbor][0 if reverse else 1])
        # self loop
        neighbors.append(node)
        weights.append(1.0)
        normalization = sum(weights) + teleport
        tranMatrix[:,node2id[node]] = teleport/(normalization*len(nodes))
        for i in range(len(neighbors)):
            tranMatrix[node2id[neighbors[i]], node2id[node]] +=\
                weights[i]/normalization
    return tranMatrix

def buildTransitionMatrix(graph, nodes, teleport=0.0, reverse=False):
    node2id = {}
    for i in range(len(nodes)):
        node2id[nodes[i]] = i
    tranMatrix = np.zeros((len(nodes), len(nodes)))
    for node in nodes:
        neighbors = [neighbor for neighbor in graph[node][1 if reverse else 0]\
                     if neighbor in node2id]
        neighbors.append(node) # self loop
        normalization = len(neighbors) + teleport
        tranMatrix[:,node2id[node]] = teleport/(normalization*len(nodes))
        p = 1.0/normalization
        for neighbor in neighbors:
            tranMatrix[node2id[neighbor], node2id[node]] += p
    return tranMatrix

def randomWalk(tranMatrix, k, home=0.0):
    assert(tranMatrix.shape[0] == tranMatrix.shape[1])
    probMatrix = np.identity(tranMatrix.shape[0])
    for i in range(k):
        # transition
        probMatrix = np.dot(tranMatrix, probMatrix)
        # teleport home
        homeMatrix = home*probMatrix
        probMatrix -= homeMatrix
        probMatrix += np.diag(homeMatrix.sum(axis=0))
    return probMatrix.transpose() # s.t. rows are distributions

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

    # create transition matrix
    print 'Building transition matrix. . .'
    from random import shuffle
    shuffle(dictionary)
    tranMatrix = buildTransitionMatrix(graph, dictionary,
                                       teleport=options.teleport,
                                       reverse=options.reverse)

    # do random walk
    print 'Performing %d step random walk. . .' % options.k
    probMatrix = randomWalk(tranMatrix, options.k, home=options.home)

    # save probMatrix
    print 'Saving walk matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=probMatrix, dictionary=dictionary)

if __name__ == '__main__':
    main()
