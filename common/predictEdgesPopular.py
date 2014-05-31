#!/usr/bin/env python

"""
Predict the edges across two graphs using a simply "popularity"-based policy.
"""

from optparse import OptionParser
import pickle
import os
import sys
import random

# local modules
from Util import loadPickle, getAndCheckFilename
from Prediction_util import getPopDictionary

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('--topn', type='int', dest='topn', default=10,
        help='Predict edges with top N most popular items.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--seed', type='int', dest='seed', default=None,
        help='Seed for random number generator.', metavar='NUM')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Display verbose output.')
    return parser

def getPopularItems(graph, popDictionary, topn, verbose=False):
    """
    Return a list of the TOPN most popular items in GRAPH as per POPDICTIONARY.
    """
    graph_pops = [(popDictionary[item], item) for item in graph]
    graph_pops.sort(key=lambda tup: tup[0], reverse=True)
    if verbose:
        print '== Popular Items =='
        for i in range(topn):
            print '%d, pop=%d' % (graph_pops[i][1], graph_pops[i][0])
    return [item for pop, item in graph_pops[0:topn]]

def predictEdges(graph, pop_items, k):
    predicted_edges = []
    for sourceItem in graph:
        for i in range(k):
            targetItem = random.choice(pop_items)
            predicted_edges.append((sourceItem, targetItem))
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options] popgraph graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    popgraph_filename = getAndCheckFilename(args[0])
    graph1_filename = getAndCheckFilename(args[1])
    graph2_filename = getAndCheckFilename(args[2])

    # seed rng
    if options.seed is not None:
        random.seed(options.seed)

    # load popularity
    print 'Loading "popularity" graph from %s. . .' % popgraph_filename
    popgraph = loadPickle(popgraph_filename)
    popDictionary = getPopDictionary(popgraph)

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)

    # get top N most popular items from graph 2
    print 'Finding most popular items in graph2. . .'
    pop_items = getPopularItems(graph2, popDictionary, options.topn,
                                verbose=options.verbose)

    # predict edges by randomly choosing from pop_items
    print 'Predicting edges. . .'
    predicted_edges = predictEdges(graph1, pop_items, options.k)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
