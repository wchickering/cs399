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
from collections import deque
from random import shuffle

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--epsilon', type='float', dest='epsilon', default=0.1,
        help='Espilon parameter for flux algorithm.', metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile', default='fluxMatrix.npz',
        help='Save file name for flux matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildFluxMatrix(graph, epsilon=0.1):
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
            shuffle(graph[n][0])
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

    # build flux matrix
    print 'Building flux matrix. . .'
    fluxMatrix = buildFluxMatrix(graph, epsilon=options.epsilon)

    # save proximity Matrix
    print 'Saving flux matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=fluxMatrix, dictionary=graph.keys())

if __name__ == '__main__':
    main()
