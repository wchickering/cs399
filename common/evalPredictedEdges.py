#!/usr/bin/env python

"""
Evaluates the predicted edges connecting the two partitioned subgraphs of the
original recommender graph.
"""

from optparse import OptionParser
import os
import sys
import math
import numpy as np

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2, metavar='NUM',
        help='Distance away in original graph to consider correct')
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Treat graphs as directed.')
    return parser

def getMatrix(filename):
    npzfile = np.load(filename)
    return npzfile['matrix']

def getDict(filename):
    npzfile = np.load(filename)
    id2item = npzfile['dictionary']
    return dict((id2item[i], i) for i in range(len(id2item)))

def evalEdges(edges, prox_mat, dictionary, k):
    correct = 0
    eps = 0.0001
    key_errors = 0
    for item1, item2 in edges:
        try:
            id1 = dictionary[item1]
            id2 = dictionary[item2]
            proximity = prox_mat[id1, id2]
            if proximity != 0 and -1*math.log(proximity) < (k + eps):
                correct += 1
        except KeyError:
            key_errors += 1
            pass
    if key_errors > 0:
        print >> sys.stderr,\
            ('WARNING: %d/%d predicted (lost) edges with one or both nodes '
             'missing from target (source) graph.') % (
                key_errors,
                len(edges)
            )
    return correct

def main():
    # Parse options
    usage = ('Usage: %prog [options] target_prox_mat.npz source_prox_mat.npz '
             'lost_edges.pickle predicted_edges.pickle')
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 4:
        parser.error('Wrong number of arguments')
    target_prox_mat_fname = getAndCheckFilename(args[0])
    source_prox_mat_fname = getAndCheckFilename(args[1])
    lost_edges_filename = getAndCheckFilename(args[2])
    predicted_edges_filename = getAndCheckFilename(args[3])

    # Load edges
    target_prox_mat = getMatrix(target_prox_mat_fname)
    target_dict = getDict(target_prox_mat_fname)
    source_prox_mat = getMatrix(source_prox_mat_fname)
    source_dict = getDict(source_prox_mat_fname)
    lost_edges = loadPickle(lost_edges_filename)
    predicted_edges = loadPickle(predicted_edges_filename)

    # Evaluate
    correct_predictions = evalEdges(predicted_edges, target_prox_mat,
                                    target_dict, options.k)
    recalled_edges = evalEdges(lost_edges, source_prox_mat,
                               source_dict, options.k)

    # compute metrics
    num_correct_predictions = len(predicted_edges)
    num_lost_edges = len(lost_edges)
    if not options.directed:
        recalled_edges /= 2
        num_lost_edges /= 2

    precision = float(correct_predictions) / num_correct_predictions
    recall = float(recalled_edges) / num_lost_edges
    f1score = 2*precision*recall/(precision + recall)

    # print evaluation results
    print '==============================================='
    print 'Correct predictions \t : %d' % correct_predictions
    print 'Total predictions \t : %d' % len(predicted_edges)
    print '%d-Precision \t\t : %0.3f' % (options.k, precision)
    print 'Recalled Edges (k=%d)\t : %d' % (options.k, recalled_edges)
    print 'Withheld edges \t\t : %d' % num_lost_edges
    print '%d-Recall \t\t : %0.3f' % (options.k, recall)
    print '%d-F1 Score \t\t : %0.3f' % (options.k, f1score)

if __name__ == '__main__':
    main()
