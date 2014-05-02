#!/usr/bin/env python

"""
Evaluates the predicted edges connecting the two partitioned subgraphs of the
original recommender graph.
"""

from optparse import OptionParser
import pickle
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

def getRelevantEdges(lost_edges, predicted_nodes):
    predicted_nodes = set(predicted_nodes)
    relevant_edges = []
    for (item1, item2) in lost_edges:
        if item1 in predicted_nodes:
            relevant_edges.append((item1, item2))
    return relevant_edges

def getPredictedNodes(predicted_edges):
    predicted_edges = np.array(predicted_edges)
    return np.unique(predicted_edges[:, 0:1])

def overlappingEdges(predicted_edges, lost_edges):
    return len(set(predicted_edges).intersection(set(lost_edges)))

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
    print 'Load edges. .'
    lost_edges = loadEdges(lost_edges_filename)
    predicted_edges = loadEdges(predicted_edges_filename)

    print 'Evaluate. .'
    # ignore lost_edges frome nodes not predicted
    predicted_nodes = getPredictedNodes(predicted_edges)
    relevant_lost_edges = getRelevantEdges(lost_edges, predicted_nodes)

    # get number of overlapping edges in these lists
    overlap = overlappingEdges(predicted_edges, relevant_lost_edges)
    
    # print evaluation results
    print '==================='
    print 'Correct predictions \t : %d' % overlap
    print 'Total predictions \t : %d' % len(predicted_edges)
    print 'Items predicted \t : %d' % len(predicted_nodes)
    print 'Guesses per item \t : %d' % (len(predicted_edges)/len(predicted_nodes))
    print 'Precision \t\t : %f' % (float(overlap) / len(predicted_edges))
    print 'Recall \t\t\t : %f' % (float(overlap) / len(relevant_lost_edges))

if __name__ == '__main__':
    main()
