#!/usr/bin/env python

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
from collections import deque

# params
epsilon = 0.1

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile',
        default='neighborMatrix.npz',
        help='Save file name for neighbor matrix.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildNeighborMatrix(graph):
    node2id = {}
    for i, node in enumerate(graph.keys()):
        node2id[node] = i
    neighborMatrix = np.identity(len(graph))
    for source in graph:
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

    # build neighbor matrix
    print 'Building neighbor matrix. . .'
    neighborMatrix = buildNeighborMatrix(graph)

    # save neighbor matrix
    print 'Saving neighbor matrix to %s. . .' % options.savefile
    np.savez(options.savefile, matrix=neighborMatrix, dictionary=graph.keys())

if __name__ == '__main__':
    main()
