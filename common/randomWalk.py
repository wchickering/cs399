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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
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
    parser.add_option('--savefile', dest='savefile', default='randomWalk.npz',
        help='Save file name for random walk matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

# Experimental transition matrix that decreases likelihood of transitioning to
# nodes with many incoming edges.
def buildTransitionMatrix2(graph, teleport=0.0, reverse=False):
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    tranMatrix = np.zeros((len(graph), len(graph)))
    for node in graph:
        neighbors = [neighbor for neighbor in graph[node][1 if reverse else 0]\
                     if neighbor in node2id]
        weights = [0.0]*len(neighbors)
        for i in range(len(neighbors)):
            weights[i] = 1.0/len(graph[neighbor][0 if reverse else 1])
        # self loop
        neighbors.append(node)
        weights.append(1.0)
        normalization = sum(weights) + teleport
        tranMatrix[:,node2id[node]] = teleport/(normalization*len(graph))
        for i in range(len(neighbors)):
            tranMatrix[node2id[neighbors[i]], node2id[node]] +=\
                weights[i]/normalization
    return tranMatrix

def buildTransitionMatrix(graph, teleport=0.0, reverse=False):
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    tranMatrix = np.zeros((len(graph), len(graph)))
    for node in graph:
        neighbors = [neighbor for neighbor in graph[node][1 if reverse else 0]]
        neighbors.append(node) # self loop
        normalization = len(neighbors) + teleport
        tranMatrix[:,node2id[node]] = teleport/(normalization*len(graph))
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
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    # create transition matrix
    print 'Building transition matrix. . .'
    tranMatrix = buildTransitionMatrix(graph, teleport=options.teleport,
                                       reverse=options.reverse)

    # do random walk
    print 'Performing %d step random walk. . .' % options.k
    probMatrix = randomWalk(tranMatrix, options.k, home=options.home)

    # save probMatrix
    print 'Saving walk matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=probMatrix, dictionary=graph.keys())

if __name__ == '__main__':
    main()
