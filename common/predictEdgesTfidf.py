#!/usr/bin/env python

"""
Predicts the edges across two graphs using item TF-IDF vectors.
"""

from optparse import OptionParser
from Queue import PriorityQueue
import pickle
import os
import sys

# local modules
from Util import loadPickle, getAndCheckFilename
from TFIDF_SimilarityCache import TFIDF_SimilarityCache

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--edges-per-node', type='float', dest='edgesPerNode',
        default=1.0,
        help='Number of predicted edges per node.', metavar='FLOAT')
    parser.add_option('--symmetric', action='store_true', dest='symmetric',
        default=False,
        help=('Predict k edges for each node in each graph connecting to a '
              'node in the other graph.'))
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--short-coeff', type='float', dest='shortCoeff',
        default=0.0,
        help='Coefficient for TF-IDF vectors from short descriptions.')
    parser.add_option('--bigrams-coeff', type='float', dest='bigramsCoeff',
        default=0.0, help='Coefficient for TF-IDF vectors from bigrams.')
    parser.add_option('--use-cosine', action='store_true',
        dest='useCosine', default=False, help='determine mapping by cosine')
    parser.add_option('--popdict', dest='popdict', default=None,
        help='Picked popularity dictionary.', metavar='FILE')
    parser.add_option('--min-pop', type='float', dest='minPop',
        default=0.0, help='Minimum popularity to be included in search engine.',
        metavar='FLOAT')
    parser.add_option('--weight-in', action='store_true', dest='weightIn',
        default=False,
        help='Weight KNN search engine results using popDictionary.')
    parser.add_option('--weight-out', action='store_true', dest='weightOut',
        default=False,
        help='Weight choice of outgoing edges using popDictionary.')
    return parser

def getTFIDFneighbors(simCache, sourceItem, targetItems, edgesPerNode,
                      weights=None, minWeight=0, reverseSim=False):
    queue = PriorityQueue()
    for targetItem in targetItems:
        if weights is not None and minWeight > 0:
            if weights[targetItem] < minWeight:
                continue
        similarity = simCache.getSim(
            targetItem if reverseSim else sourceItem,
            sourceItem if reverseSim else targetItem
        )
        if weights is not None:
            similarity *= weights[targetItem]
        queue.put((similarity, targetItem))
        if queue.qsize() > edgesPerNode:
            queue.get()
    neighbors = []
    while not queue.empty():
        (similarity, targetItem) = queue.get()
        neighbors.append(targetItem)
    return neighbors

def predictEdges(simCache, items1, items2, edgesPerNode, symmetric=False,
                 weights=None, weightIn=False, weightOut=False, minWeight=0):
    predictedEdges = []
    if weights is not None and weightOut:
        print 'Predicting edges (weighted outgoing). . . '
        totalPredictions = int(len(items1)*edgesPerNode)
        if symmetric:
            totalPredictions += int(len(items2)*edgesPerNode)
        totalPopularity = 0.0
        for item1 in items1:
            totalPopularity += weights[item1]
        if symmetric:
            for item2 in items2:
                totalPopularity += weights[item2]
        for item1 in items1:
            numPredictions = int(round(totalPredictions*\
                                        weights[item1]/\
                                        totalPopularity))
            if numPredictions > 0:
                neighbors = getTFIDFneighbors(
                    simCache,
                    item1,
                    items2,
                    numPredictions,
                    weights=weights if weightIn else None,
                    minWeight=minWeight,
                    reverseSim=False
                )
                predictedEdges += [(item1, n) for n in neighbors]
        if symmetric:
            for item2 in items2:
                numPredictions = int(round(totalPredictions*\
                                            weights[item2]/\
                                            totalPopularity))
                if numPredictions > 0:
                    neighbors = getTFIDFneighbors(
                        simCache,
                        item2,
                        items1,
                        numPredictions,
                        weights=weights if weightIn else None,
                        minWeight=minWeight,
                        reverseSim=True
                    )
                    predictedEdges += [(item2, n) for n in neighbors]
    else:
        print 'Predicting edges (uniform outgoing). . .'
        for item1 in items1:
            neighbors = getTFIDFneighbors(
                simCache,
                item1,
                items2,
                edgesPerNode,
                weights=weights if weightIn else None,
                minWeight=minWeight,
                reverseSim=False
            )
            predictedEdges += [(item1, n) for n in neighbors]
        if symmetric:
            for item2 in items2:
                neighbors = getTFIDFneighbors(
                    item2,
                    items1,
                    edgesPerNode,
                    weights=weights if weightIn else None,
                    minWeight=minWeight,
                    reverseSim=True
                )
                predictedEdges += [(item2, n) for n in neighbors]
    return predictedEdges

def main():
    # Parse options
    usage = 'Usage: %prog [options] tfidfs.pickle graph1.pickle graph2.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    tfidfsFilename = getAndCheckFilename(args[0])
    graphFilename1 = getAndCheckFilename(args[1])
    graphFilename2 = getAndCheckFilename(args[2])

    # load TF-IDF vectors
    print 'Loading TF-IDF vectors from %s. . .' % tfidfsFilename
    tfidfs = loadPickle(tfidfsFilename)

    # load graphs
    print 'Loading graph1 from %s. . .' % graphFilename1
    graph1 = loadPickle(graphFilename1)
    print 'Loading graph2 from %s. . .' % graphFilename2
    graph2 = loadPickle(graphFilename2)

    # get popularity
    if options.popdict:
        print 'Loading popularity dictionary from %s. . .' % options.popdict
        popDictionary = loadPickle(options.popdict)
    else:
        popDictionary = None

    # precompute TF-IDF similarities
    print 'Computing item similarities in TF-IDF space. . .'
    simCache = TFIDF_SimilarityCache(
        tfidfs,
        shortCoeff=options.shortCoeff,
        bigramsCoeff=options.bigramsCoeff,
        useCosine=options.useCosine
    )
    simCache.preComputeSims(graph1.keys(), graph2.keys())

    # predict edges
    predictedEdges = predictEdges(
        simCache,
        graph1.keys(),
        graph2.keys(),
        options.edgesPerNode,
        symmetric=options.symmetric,
        weights=popDictionary,
        weightIn=options.weightIn,
        weightOut=options.weightOut,
        minWeight=options.minPop
    )

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predictedEdges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
