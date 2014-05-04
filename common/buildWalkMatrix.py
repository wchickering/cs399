#!/usr/bin/env python

"""
Performs one of several types of walk matrices for a given matrix.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import math
from random import shuffle
from collections import deque

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--type', dest='type', default='random',
        help=('Type of walk: random (default), transition, adjacency, '
              'proximity, neighbor, or flux.'), metavar='TYPE')
    parser.add_option('--steps', type='int', dest='steps', default=10,
        help='Number of steps in random walk.', metavar='NUM')
    parser.add_option('--teleport', type='float', dest='teleport',
        default=0.0, help='Weight of additional "teleportation" edge.',
        metavar='FLOAT')
    parser.add_option('--home', type='float', dest='home', default=0.0,
        help='Probability of teleporting back to starting node.',
        metavar='FLOAT')
    parser.add_option('--reverse', action='store_true', dest='reverse',
        default=False, help='Follow incoming edges.')
    parser.add_option('--decay', type='float', dest='decay', default=1.0,
        help='Decay constant for proximity matrix.', metavar='FLOAT')
    parser.add_option('--epsilon', type='float', dest='epsilon', default=0.1,
        help='Espilon parameter for neighbor or flux matrix.', metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile', default='walkMatrix.npz',
        help='Save file name for walk matrix.', metavar='FILE')
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

def randomWalk(tranMatrix, steps, home=0.0):
    """
    Performs a random walk on a graph represented by the transition matrix
    TRANMATRIX to yield a matrix of probabilities distributions over the graph
    representing the likelihood a walker starting at node i ends up at node j
    after STEPS step. After each step, the walker teleports back to its starting
    node with probability HOME.
    """
    assert(tranMatrix.shape[0] == tranMatrix.shape[1])
    probMatrix = np.identity(tranMatrix.shape[0])
    for i in range(steps):
        # transition
        probMatrix = np.dot(tranMatrix, probMatrix)
        # teleport home
        homeMatrix = home*probMatrix
        probMatrix -= homeMatrix
        probMatrix += np.diag(homeMatrix.sum(axis=0))
    return probMatrix.transpose() # s.t. rows are distributions

def buildAdjacencyMatrix(graph, reverse=False):
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    adjacencyMatrix = np.zeros((len(graph), len(graph)))
    for source in graph:
        for neighbor in graph[source][1 if reverse else 0]:
            adjacencyMatrix[node2id[source],node2id[neighbor]] = 1
    return adjacencyMatrix

def buildProximityMatrix(graph, decay=1.0, reverse=False):
    """
    Performs a breadth-first-search starting from each node to construct a
    matrix of proximities/closeness from each node i to each node j.
    """
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    proxMatrix = np.zeros((len(graph), len(graph)))
    nodes = graph.keys()
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
            shuffle(graph[n][1 if reverse else 0])
            for neighbor in graph[n][1 if reverse else 0]:
                if neighbor in visited: continue
                q.appendleft((neighbor, x+1))
    return proxMatrix

def buildNeighborMatrix(graph, epsilon=0.1, reverse=False):
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    neighborMatrix = np.identity(len(graph))
    for source in graph:
        for neighbor in graph[source][1 if reverse else 0]:
            neighborMatrix[node2id[source],node2id[neighbor]] =\
                (1.0 - epsilon)/len(graph[source][0])
    return neighborMatrix

def buildFluxMatrix(graph, epsilon=0.1, reverse=False):
    """
    Performs a breadth-first-search starting from each node to construct a
    matrix of "flux" from each node i to each node j.
    """
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    fluxMatrix = np.zeros((len(graph), len(graph)))
    nodes = graph.keys()
    shuffle(nodes)
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
            shuffle(graph[n][1 if reverse else 0])
            for neighbor in graph[n][1 if reverse else 0]:
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
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    walkMatrix = None
    if options.type == 'random' or options.type == 'transition':
        # create transition matrix
        print 'Building transition matrix. . .'
        tranMatrix = buildTransitionMatrix(graph, teleport=options.teleport,
                                           reverse=options.reverse)
        if options.type == 'transition':
            walkMatrix = tranMatrix

    if options.type == 'random':
        # do random walk
        print 'Performing %d step random walk. . .' % options.steps
        walkMatrix = randomWalk(tranMatrix, options.steps, home=options.home)
    elif options.type == 'adjacency':
        # create adjacency matrix
        print 'Creating adjacency matrix. . .'
        walkMatrix = buildAdjacencyMatrix(graph, reverse=options.reverse)
    elif options.type == 'proximity':
        # build proximity matrix
        print 'Building proximity matrix. . .'
        walkMatrix = buildProximityMatrix(graph, decay=options.decay,
                                          reverse=options.reverse)
    elif options.type == 'neighbor':
        # build neighbor matrix
        print 'Building neighbor matrix. . .'
        walkMatrix = buildNeighborMatrix(graph, epsilon=options.epsilon,
                                         reverse=options.reverse)
    elif options.type == 'flux':
        # build flux matrix
        print 'Building flux matrix. . .'
        walkMatrix = buildFluxMatrix(graph, epsilon=options.epsilon,
                                     reverse=options.reverse)

    if walkMatrix is not None:
        # save probMatrix
        print 'Saving walk matrix to %s. . .' % options.savefile
        np.savez(options.savefile, matrix=walkMatrix, dictionary=graph.keys())

if __name__ == '__main__':
    main()
