#!/usr/bin/env python

"""
Maps one topic/concept space to another using the product TF-IDF vectors.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
from sklearn.preprocessing import normalize

# local modules
from Util import loadPickle, getAndCheckFilename
from TFIDF_SimilarityCache import TFIDF_SimilarityCache

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile', default='topicMap.pickle',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Display topic map.')
    parser.add_option('--identity', action='store_true', dest='identity',
        default=False, help='Produce identity matrix with correct dimensions.')
    parser.add_option('--random', action='store_true', dest='random',
        default=False, help='Produce random matrix with correct dimensions.')
    parser.add_option('--short-coeff', type='float', dest='shortCoeff',
        default=0.0,
        help='Coefficient for TF-IDF vectors from short descriptions.')
    parser.add_option('--bigrams-coeff', type='float', dest='bigramsCoeff',
        default=0.0, help='Coefficient for TF-IDF vectors from bigrams.')
    parser.add_option('--hood-coeff', type='float', dest='hoodCoeff',
        default=0.0, help='Coefficient for TF-IDF vectors from neighborhood.')
    parser.add_option('--use-cosine', action='store_true',
        dest='useCosine', default=False, help='determine mapping by cosine')
    parser.add_option('--normalize', action='store_true', dest='normalize',
        default=False,
        help='Normalize column vectors of transformation matrix.')
    parser.add_option('--ortho', action='store_true', dest='ortho',
        default=False, help='Orthogonalize the transformation matrix.')
    parser.add_option('--beta', type='float', dest='beta', default=None,
        help='Parameter for sigmoid to apply to weighted similarities.',
        metavar='NUM')
    parser.add_option('--seed', type='int', dest='seed', default=None,
        help='Seed for random number generator.', metavar='NUM')
    return parser

def loadLSIModel(modelFilename):
    npzfile = np.load(modelFilename)
    model = npzfile['u']
    items = npzfile['dictionary']
    return model, items

def orthogonalize(m):
    from scipy.linalg import sqrtm, inv
    return m.dot(inv(sqrtm(m.T.dot(m))))

def sigmoid(x, beta=1.0):
    u = np.exp(-x/beta)
    return (1.0 - u)/(1.0 + u)

def getTopicMap(model1, dictionary1, model2, dictionary2, simCache, beta=None):
    topicMap = []
    for topic1 in range(model1.shape[1]):
        mapColumn = []
        for topic2 in range(model2.shape[1]):
            # weightMatrix entries are products of the pair's topic strengths
            weightMatrix = np.outer(model1[:,topic1],model2[:,topic2])
            # weightedSimMatrix entries are products of topicStrengths and
            # TF-IDF inner products
            weightedSimMatrix = np.multiply(weightMatrix, simCache.sims)
            if beta is not None:
                # apply sigmoid to each weighted similarity
                weightedSimMatrix = sigmoid(weightedSimMatrix, beta)
            mapColumn.append(np.sum(weightedSimMatrix))
        topicMap.append(mapColumn)
    return np.array(topicMap).transpose()

def main():
    # Parse options
    usage = 'Usage: %prog [options] tfidfs.pickle model1.npz model2.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    tfidfsFilename = getAndCheckFilename(args[0])
    modelFilename1 = getAndCheckFilename(args[1])
    modelFilename2 = getAndCheckFilename(args[2])

    # load TF-IDF vectors
    print 'Loading TF-IDF vectors from %s. . .' % tfidfsFilename
    tfidfs = loadPickle(tfidfsFilename)

    # load models
    print 'Loading LSI model from %s. . .' % modelFilename1
    model1, items1 = loadLSIModel(modelFilename1)
    print 'Loading LSI model from %s. . .' % modelFilename2
    model2, items2 = loadLSIModel(modelFilename2)

    # seed rng
    if options.seed is not None:
        np.random.seed(options.seed)

    # construct map
    if options.identity:
        print 'Creating identity map. . .'
        topicMap = np.identity(model1.shape[1])
    elif options.random:
        print 'Creating random map. . .'
        topicMap = np.random.rand(model1.shape[1], model2.shape[1])
    else:
        # precompute TF-IDF similarities
        print 'Computing item similarities in TF-IDF space. . .'
        simCache = TFIDF_SimilarityCache(
            tfidfs,
            shortCoeff=options.shortCoeff,
            bigramsCoeff=options.bigramsCoeff,
            hoodCoeff=options.hoodCoeff,
            useCosine=options.useCosine
        )
        simCache.preComputeSims(items1, items2)

        print 'Mapping topics between catalogs. . .'
        # build topic map
        topicMap = getTopicMap(model1, items1, model2, items2, simCache,
                               beta=options.beta)

    if options.normalize:
        # normalize map
        print 'Normalizing topic map. . .'
        topicMap = normalize(topicMap, axis=0)

    if options.ortho:
        # orthogonalize map
        print 'Orthogonalizing topic map. . .'
        topicMap = orthogonalize(topicMap)

    # save topic map to disk
    print 'Saving topic map to %s. . .' % options.savefile
    pickle.dump(topicMap, open(options.savefile, 'w'))

    # display results
    if options.verbose:
        for i in range(len(topicMap)):
            print '  '.join('%.3f' % x for x in topicMap[i])

if __name__ == '__main__':
    main()
