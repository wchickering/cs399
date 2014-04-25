#!/usr/bin/env python

"""
Evaluates the predicted edges connecting the two partitioned subgraphs of the
original recommender graph.
"""

from optparse import OptionParser
from collections import deque
import pickle
import random
import os
import sys
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def loadEdges(fname):
    with open(fname, 'r') as f:
        edges = pickle.load(f)
    return edges

def overlappingEdges(edges1, edges2):
    i = 0
    j = 0
    edges1_len = len(edges1)
    edges2_len = len(edges2)
    overlaps = 0
    while i < edges1_len and j < edges2_len:
        if edges1[i] == edges2[j]:
            i += 1
            j += 1
            overlaps += 1
        elif edges1[1] < edges2[j]:
            i += 1
        else:
            j += 1
    return overlaps

def getRelevantLostEdges(lost_edges, predicted_nodes):
    relevant_lost_edges = []
    i = 0
    j = 0
    lost_edges_len = len(lost_edges)
    predicted_nodes_len = len(predicted_nodes)
    while i < lost_edges_len and j < predicted_nodes_len:
        if lost_edges[i][0] < predicted_nodes[j]:
            i += 1
        else:
            while i < lost_edges_len and lost_edges[i][0] == predicted_nodes[j]:
                i += 1
            j += 1

def getPredictedNodes(predicted_edges):
    predicted_edges = np.array(predicted_edges)
    return np.unique(predicted_edges[:, 0:1])

def main():
    # Parse options
    usage = 'Usage: %prog lost_edges.pickle predicted_edges.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    lost_edges_filename = args[0]
    predicted_edges_filename = args[1]
    if not os.path.isfile(lost_edges_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % lost_edges_filename
    if not os.path.isfile(predicted_edges_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % predicted_edges_filename

    # load edges
    lost_edges = loadEdges(lost_edges_filename)
    predicted_edges = loadEdges(predicted_edges_filename)

    # sort edges
    lost_edges.sort()
    predicted_edges.sort()

    # ignore lost_edges frome nodes not predicted
    predicted_nodes = getPredictedNodes(predicted_edges)
    relevant_lost_edges = getRelevantLostEdges(lost_edges, predicted_nodes)

    # get number of overlapping edges in these lists
    overlap = overlappingEdges(lost_edges, predicted_edges)
    
    # print evaluation results
    print 'Correct predictions = %d / %d' % (overlap, len(predicted_edges))
    print 'Recalled lost edges = %d / %d' % (overlap, len(lost_edges))
    print 'Precision = %f' % (float(overlap) / len(predicted_edges))
    print 'Recall = %f' % (float(overlap) / len(lost_edges))

if __name__ == '__main__':
    main()
