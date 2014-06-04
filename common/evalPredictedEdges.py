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

def evalEdges(edges, proxMat, dictionary, k):
    correct = 0
    eps = 0.0001
    keyErrors = 0
    for item1, item2 in edges:
        try:
            id1 = dictionary[item1]
            id2 = dictionary[item2]
            proximity = proxMat[id1, id2]
            if proximity != 0 and -1*math.log(proximity) < (k + eps):
                correct += 1
        except KeyError:
            keyErrors += 1
            pass
    if keyErrors > 0:
        print >> sys.stderr,\
            ('WARNING: %d/%d predicted (lost) edges with one or both nodes '
             'missing from target (source) graph.') % (
                keyErrors,
                len(edges)
            )
    return correct

def main():
    # Parse options
    usage = ('Usage: %prog [options] targetProxMat.npz sourceProxMat.npz '
             'lostEdges.pickle predictedEdges.pickle')
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 4:
        parser.error('Wrong number of arguments')
    targetProxMatFilename = getAndCheckFilename(args[0])
    sourceProxMatFilename = getAndCheckFilename(args[1])
    lostEdgesFilename = getAndCheckFilename(args[2])
    predictedEdgesFilename = getAndCheckFilename(args[3])

    # Load edges
    targetProxMat = getMatrix(targetProxMatFilename)
    targetDict = getDict(targetProxMatFilename)
    sourceProxMat = getMatrix(sourceProxMatFilename)
    sourceDict = getDict(sourceProxMatFilename)
    lostEdges = loadPickle(lostEdgesFilename)
    predictedEdges = loadPickle(predictedEdgesFilename)

    # Evaluate
    correctPredictions = evalEdges(predictedEdges, targetProxMat,
                                    targetDict, options.k)
    recalledEdges = evalEdges(lostEdges, sourceProxMat,
                               sourceDict, options.k)

    # get results
    numCorrectPredictions = len(predictedEdges)
    numLostEdges = len(lostEdges)
    if not options.directed:
        recalledEdges /= 2
        numLostEdges /= 2

    # compute metrics
    precision = float(correctPredictions) / numCorrectPredictions
    recall = float(recalledEdges) / numLostEdges
    if precision == 0.0 and recall == 0.0:
        f1score = 0.0
    else:
        f1score = 2*precision*recall/(precision + recall)

    # display results
    print '==============================================='
    print 'Correct predictions \t : %d' % correctPredictions
    print 'Total predictions \t : %d' % len(predictedEdges)
    print '%d-Precision \t\t : %0.3f' % (options.k, precision)
    print 'Recalled Edges (k=%d)\t : %d' % (options.k, recalledEdges)
    print 'Withheld edges \t\t : %d' % numLostEdges
    print '%d-Recall \t\t : %0.3f' % (options.k, recall)
    print '%d-F1 Score \t\t : %0.3f' % (options.k, f1score)

if __name__ == '__main__':
    main()
