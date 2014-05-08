#!/usr/bin/env python

"""
Evaluates the predicted edges connecting the two partitioned subgraphs of the
original recommender graph.
"""

from optparse import OptionParser
import pickle
import os
import sys
import math
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', dest='k', default=1, metavar='NUM',
        help='Distance away in original graph to consider correct')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        obj = pickle.load(f)
    return obj

def getMatrix(filename):
    npzfile = np.load(filename)
    return npzfile['matrix']

def getDict(filename):
    npzfile = np.load(filename)
    id2item = npzfile['dictionary']
    return dict((id2item[i], i) for i in range(len(id2item)))

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

def correctPredictions(predicted_edges, proximity_mat, dictionary, k):
    correct = 0
    eps = 0.0001
    for item1, item2 in predicted_edges:
        id1 = dictionary[item1]
        id2 = dictionary[item2]
        proximity = proximity_mat[id1, id2]
        if proximity != 0 and -1*math.log(proximity) < (k + eps):
            correct += 1
    return correct

def main():
    # Parse options
    usage = 'Usage: %prog [options] proximity_mat.pickle predicted_edges.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    proximity_mat_fname = args[0]
    predicted_edges_filename = args[1]
    if not os.path.isfile(proximity_mat_fname):
        parser.error('Cannot find %s' % proximity_mat_fname)
    if not os.path.isfile(predicted_edges_filename):
        parser.error('Cannot find %s' % predicted_edges_filename)

    # Load edges
    print 'Load pickles. .'
    proximity_mat = getMatrix(proximity_mat_fname)
    dictionary = getDict(proximity_mat_fname)
    predicted_edges = loadPickle(predicted_edges_filename)

    # Evaluate
    print 'Evaluate predictions. .'
    correct = correctPredictions(predicted_edges, proximity_mat, dictionary,
            int(options.k))

    predicted_nodes = getPredictedNodes(predicted_edges)

    # print evaluation results
    print '==================='
    print 'k \t\t\t : %s' % options.k
    print 'Correct predictions \t : %d' % correct
    print 'Total predictions \t : %d' % len(predicted_edges)
    print 'Items predicted \t : %d' % len(predicted_nodes)
    print 'Guesses per item \t : %d' % (len(predicted_edges)/len(predicted_nodes))
    #print 'Withheld edges \t\t : %d' % (len(relevant_lost_edges))
    print 'Precision \t\t : %f' % (float(correct) / len(predicted_edges))
    #print 'Recall \t\t\t : %f' % (float(correct) / len(relevant_lost_edges))

if __name__ == '__main__':
    main()
