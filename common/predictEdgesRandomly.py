#!/usr/bin/env python

"""
Randomly predicts the edges across two paritionaed graphs
"""

from optparse import OptionParser
import pickle
import os
import sys
import random

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('--seed', type='int', dest='seed', default=None,
        help='Seed for random number generator.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        obj = pickle.load(f)
    return obj

def predictRandomEdges(graph1, graph2, k):
    predicted_edges = []
    for node1 in graph1:
        neighbors = random.sample(graph2.keys(), k)
        predicted_edges += [(node1, n) for n in neighbors]
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph1.pickle graph2.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments') 
    graph1_filename = args[0]
    if not os.path.isfile(graph1_filename):
        parser.error('Cannot find %s' % graph1fname)
    graph2_filename = args[1]
    if not os.path.isfile(graph2_filename):
        parser.error('Cannot find %s' % graph2_filename)

    # seed rng
    if options.seed is not None:
        random.seed(options.seed)

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)

    # predict edges
    print 'Randomly predicting edges. . .'
    predicted_edges = predictRandomEdges(graph1, graph2, options.k)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
