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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='float', dest='k', default=2.0,
        help='Number of predicted edges per node.', metavar='FLOAT')
    parser.add_option('--topn', type='int', dest='topn', default=10,
        help='Predict edges with top N most popular items.', metavar='NUM')
    parser.add_option('--symmetric', action='store_true', dest='symmetric',
        default=False,
        help=('Predict k edges for each node in each graph connecting to a '
              'node in the other graph.'))
    parser.add_option('--weight-out', action='store_true', dest='weightOut',
        default=False,
        help='Weight choice of outgoing edges using popDictionary.')
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
    graphPops = [(popDictionary[item], item) for item in graph]
    graphPops.sort(key=lambda tup: tup[0], reverse=True)
    if verbose:
        print '== Popular Items =='
        for i in range(topn):
            print '%d, pop=%0.3f' % (graphPops[i][1], graphPops[i][0])
    return [item for pop, item in graphPops[0:topn]]

def predictEdges(graph1, graph2, popItems1, popItems2, k,
                 weights=None, symmetric=False):
    predictedEdges = []
    if weights is not None:
        print 'Predicting edges (weighted outgoing). . .'
        totalPredictions = int(len(graph1)*k)
        if symmetric:
            totalPredictions += int(len(graph2)*k)
        totalPopularity = 0.0
        for item1 in graph1:
            totalPopularity += weights[item1]
        if symmetric:
            for item2 in graph2:
                totalPopularity += weights[item2]
        for item1 in graph1:
            numPredictions = int(round(totalPredictions*\
                                        weights[item1]/\
                                        totalPopularity))
            for i in range(numPredictions):
                predictedEdges.append((item1, random.choice(popItems2)))
        if symmetric:
            for item2 in graph2:
                numPredictions = int(round(totalPredictions*\
                                           weights[item2]/\
                                           totalPopularity))
                for i in range(numPredictions):
                    predictedEdges.append((item2, random.choice(popItems1)))
    else:
        print 'Predicting edges (uniform outgoing). . .'
        for item1 in graph1:
            for i in range(int(k)):
                predictedEdges.append((item1, random.choice(popItems2)))
    return predictedEdges

def main():
    # Parse options
    usage = ('Usage: %prog [options] popDictionary.pickle '
             'graph1.pickle graph2.pickle')
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    popdictFilename = getAndCheckFilename(args[0])
    graphFilename1 = getAndCheckFilename(args[1])
    graphFilename2 = getAndCheckFilename(args[2])

    # seed rng
    if options.seed is not None:
        random.seed(options.seed)

    # load popularity
    print 'Loading popularity dictionary from %s. . .' % popdictFilename
    popDictionary = loadPickle(popdictFilename)

    # load graphs
    print 'Loading graph1 from %s. . .' % graphFilename1
    graph1 = loadPickle(graphFilename1)
    print 'Loading graph2 from %s. . .' % graphFilename2
    graph2 = loadPickle(graphFilename2)

    # get top N most popular items from graph 2
    print 'Finding most popular items. . .'
    popItems2 = getPopularItems(graph2, popDictionary, options.topn,
                                verbose=options.verbose)
    if options.symmetric:
        popItems1 = getPopularItems(graph1, popDictionary, options.topn,
                                    verbose=options.verbose)
    else:
        popItems1 = None

    # predict edges by randomly choosing from pop_items
    predictedEdges = predictEdges(
        graph1,
        graph2,
        popItems1,
        popItems2,
        options.k,
        weights=popDictionary if options.weightOut else None,
        symmetric=options.symmetric
    )

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predictedEdges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
