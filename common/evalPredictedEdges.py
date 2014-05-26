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

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', dest='k', default=2, metavar='NUM',
        help='Distance away in original graph to consider correct')
    return parser

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
    usage = ('Usage: %prog [options] proximity_mat.npz predicted_edges.pickle '
             'lost_edges.pickle')
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    proximity_mat_fname = getAndCheckFilename(args[0])
    predicted_edges_filename = getAndCheckFilename(args[1])
    lost_edges_filename = getAndCheckFilename(args[2])

    # Load edges
    proximity_mat = getMatrix(proximity_mat_fname)
    dictionary = getDict(proximity_mat_fname)
    predicted_edges = loadPickle(predicted_edges_filename)
    lost_edges = loadPickle(lost_edges_filename)

    # Evaluate
    correct = correctPredictions(predicted_edges, proximity_mat, dictionary,
            int(options.k))

    predicted_nodes = getPredictedNodes(predicted_edges)
    relevant_lost_edges = getRelevantEdges(lost_edges, predicted_nodes)
 
    # print evaluation results
    print '==================='
    print 'Correct predictions \t : %d' % correct
    print 'Total predictions \t : %d' % len(predicted_edges)
    print 'Items predicted \t : %d' % len(predicted_nodes)
    print 'Guesses per item \t : %d' % (len(predicted_edges)/len(predicted_nodes))
    print 'Withheld edges \t\t : %d' % (len(relevant_lost_edges))
    print '%s-Precision \t\t : %f' % (options.k, (float(correct) /
        len(predicted_edges)))
    print '%s-Recall \t\t : %f' % (options.k, (float(correct) /
        len(relevant_lost_edges)))

if __name__ == '__main__':
    main()
