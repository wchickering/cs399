#!/usr/bin/env python

"""
Re-constructs a directed recommendation graph from a set of random walks over
the graph.
"""

from optparse import OptionParser
import numpy as np
import pickle
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--numedges', type='int', dest='numedges',
        default=4, help='Number of outgoing edges per node.', metavar='NUM')
    parser.add_option('-o', '--output', dest='outfilename',
        default='graphFromWalk.pickle',
        help='Output pickle file containing re-constructed graph.',
        metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def buildCovMatrix(distMatrix):
    mu = np.sum(distMatrix, axis=1)/distMatrix.shape[1]
    normMatrix = distMatrix - mu
    return np.dot(normMatrix.transpose(), normMatrix)

def getNeighbors(matrix, dictionary, numedges):
    covMatrix = buildCovMatrix(matrix)
    candidates = np.argsort(covMatrix, axis=1)[:,0:numedges+1]
    neighbors = []
    for i in range(len(candidates)):
        # preclude self-loops
        nbrs = [c for c in candidates[i] if c != i]
        neighbors.append([dictionary[n] for n in nbrs][0:numedges])
    return neighbors
        
def makeGraph(dictionary, neighbors):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    for index, source in dictionary.items():
        if source not in graph:
            node_cnt += 1
            graph[source] = ([],[])
        for neighbor in neighbors[index]:
            graph[source][0].append(neighbor)
            if neighbor not in graph:
                node_cnt += 1
                graph[neighbor] = ([],[])
            graph[neighbor][1].append(source)
            edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] randomWalk.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('ERROR: Wrong number of arguments.')
    filename = args[0]
    if not os.path.isfile(filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % filename
        return

    # load walk matrix
    print 'Loading matrix from %s. . .' % filename
    npzfile = np.load(filename)
    matrix = npzfile['matrix']
    d = npzfile['dictionary']
    dictionary = {}
    for i in range(len(d)):
        dictionary[i] = int(d[i])
        
    # find neighbors
    print 'Finding node neighbors. . .'
    neighbors = getNeighbors(matrix, dictionary, options.numedges)

    # make graph
    print 'Making graph. . .'
    graph = makeGraph(dictionary, neighbors)

    # save graph
    print 'Saving graph to %s. . .' % options.outfilename
    pickle.dump(graph, open(options.outfilename, 'w'))

if __name__ == '__main__':
    main()

