#!/usr/bin/env python

"""
TODO: Update this description!
Maps one topic space to another using TF-IDF vector representations of each
topic and comparing each. The output is a matrix with unit length columns by the
L1 norm. Multiplying this matrix by a topic column vector of catalogue 1 gives a
topic vector in catalogue 2's space.
"""

from optparse import OptionParser
from Queue import PriorityQueue
import pickle
import os
import sys
import math
import numpy as np
import random
from sklearn.preprocessing import normalize

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile', default='topicMap.pickle',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Print top words')
    parser.add_option('--identity', action='store_true', dest='identity',
        default=False, help='Produce identity matrix with correct dimensions.')
    parser.add_option('--random', action='store_true', dest='random',
        default=False, help='Produce random matrix with correct dimensions.')
    parser.add_option('-d', '--use-distance', action='store_true',
        dest='useDistance', default=False, help='determine mapping by distance')
    parser.add_option('-c', '--use-cosine', action='store_true',
        dest='useCosine', default=False, help='determine mapping by cosine')
    parser.add_option('--normalize', action='store_true', dest='normalize',
        default=False,
        help='Normalize column vectors of transformation matrix.')
    parser.add_option('--max-connections', type='int', dest='maxConnections',
        default=None, help='Max number of topics a single topic can map to.', 
        metavar='NUM')
    parser.add_option('--seed', type='int', dest='seed', default=None,
        help='Seed for random number generator.', metavar='NUM')
    return parser

def getIdentityMap(shape):
    identMap = []
    for i in range(shape[0]):
        columnVector = []
        for j in range(shape[1]):
            if j == i:
                columnVector.append(1.0)
            else:
                columnVector.append(0.0)
        identMap.append(columnVector)
    return identMap

def getRandomMap(shape):
    return [[random.random() for j in range(shape[1])] for i in range(shape[0])]

def topicInnerProduct(tfidf1, tfidf2):
    inner_product = 0.0
    for word in tfidf1:
        if word in tfidf2:
            inner_product += float(tfidf1[word])*float(tfidf2[word])
    return inner_product

def topicCosineSimilarity(tfidf1, tfidf2):
    similarity = 0.0
    len1 = 0.0
    len2 = 0.0
    for term in tfidf1:
        len1 += float(tfidf1[term])*float(tfidf1[term])
        if term in tfidf2:
            similarity += float(tfidf1[term])*float(tfidf2[term])
    for term in tfidf2:
        len2 += float(tfidf2[term])*float(tfidf2[term])
    return similarity/(math.sqrt(len1)*math.sqrt(len2))

def topicDistance(tfidf1, tfidf2):
    sqrDistance = 0.0
    for term in tfidf1:
        p1 = float(tfidf1[term])
        if term not in tfidf2:
            sqrDistance += p1*p1
        else:
            p2 = float(tfidf2[term])
            sqrDistance += (p1-p2) * (p1-p2)
    for term in tfidf2:
        if term not in tfidf1:
            p2 = float(tfidf2[term])
            sqrDistance += p2*p2
    return math.sqrt(sqrDistance)

def getTopicMap(topicTFIDFs1, topicTFIDFs2, maxConnections=None,
                normalize=False, useDistance=False, useCosine=False):
    topicMap = [] 
    for tfidf1 in topicTFIDFs1:
        topicVector = []
        for tfidf2 in topicTFIDFs2:
            if useDistance:
                similarity = 1.0/topicDistance(dict(tfidf1), dict(tfidf2))
            elif useCosine:
                similarity = topicCosineSimilarity(dict(tfidf1), dict(tfidf2))
            else:
                similarity = topicInnerProduct(dict(tfidf1), dict(tfidf2))
            topicVector.append(similarity)
        # if all zeros, then set all similarities to # 1.0/len(topicVector)
        if np.linalg.norm(topicVector, 1) == 0.0:
            topicVector = [1.0/len(topicVector) for x in topicVector]
        if maxConnections is not None and maxConnections < len(topicVector):
            # limit number of connections
            queue = PriorityQueue()
            for idx in range(len(topicVector)):
                similarity = topicVector[idx]
                queue.put((similarity, idx))
                if queue.qsize() > maxConnections:
                    (similarity, idx) = queue.get()
                    topicVector[idx] = 0.0
        if normalize:
            topicMap.append(topicVector/np.linalg.norm(topicVector))
        else:
            topicMap.append(topicVector)
    return np.array(topicMap).transpose()

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicTFIDFs1.pickle topicTFIDFs2.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    topicTFIDFs1_fname = getAndCheckFilename(args[0])
    topicTFIDFs2_fname = getAndCheckFilename(args[1])

    # seed rng
    if options.seed is not None:
        random.seed(options.seed)

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topicTFIDFs1_fname
    topicTFIDFs1 = loadPickle(topicTFIDFs1_fname)
    print 'Loading topics of second catalogue from %s. . .' % topicTFIDFs2_fname
    topicTFIDFs2 = loadPickle(topicTFIDFs2_fname)

    # contruct map
    if options.identity:
        print 'Creating identity map. . .'
        topicMap = getIdentityMap((len(topicTFIDFs1), len(topicTFIDFs2)))
    elif options.random:
        print 'Creating random map. . .'
        topicMap = getRandomMap((len(topicTFIDFs1), len(topicTFIDFs2)))
    else:
        print 'Mapping topics between catalogues. . .'
        topicMap = getTopicMap(
            topicTFIDFs1,
            topicTFIDFs2,
            maxConnections=options.maxConnections,
            normalize=options.normalize,
            useDistance=options.useDistance,
            useCosine=options.useCosine
        )

    # save map to disk
    print 'Saving topic map to %s. . .' % options.savefile
    pickle.dump(topicMap, open(options.savefile, 'w'))

    # display results
    if options.verbose:
        for i in range(len(topicMap)):
            print '  '.join('%.3f' % x for x in topicMap[i])

if __name__ == '__main__':
    main()
