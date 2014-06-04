#!/usr/bin/env python
"""
Randomly predicts the edges across two paritionaed graphs
"""

from optparse import OptionParser
import pickle
import os
import sys
import random

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--edges-per-node', type='float', dest='edgesPerNode',
        default=1.0, help='Number of predicted edges per node.',
        metavar='FLOAT')
    parser.add_option('--seed', type='int', dest='seed', default=None,
        help='Seed for random number generator.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--popgraph', dest='popgraph', default=None,
        help='Picked graph representing item "popularity".', metavar='FILE')
    return parser

def predictRandomEdges(graph1, graph2, edgesPerNode):
    predicted_edges = []
    for node1 in graph1:
        neighbors = random.sample(graph2.keys(), int(edgesPerNode))
        predicted_edges += [(node1, n) for n in neighbors]
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph1.pickle graph2.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments') 

    graph1_filename = getAndCheckFilename(args[0])
    graph2_filename = getAndCheckFilename(args[1])

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
    predicted_edges = predictRandomEdges(graph1, graph2, options.edgesPerNode)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
