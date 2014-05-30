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

# local modules
from Util import loadPickle, getAndCheckFilename
from sklearn.preprocessing import normalize

# params
def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile',
        default='data/topic_map.pickle',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Print top words')
    parser.add_option('-d', '--by_distance', action='store_true',
        dest='by_distance', default=False, help='determine mapping by distance')
    parser.add_option('-c', '--by_cosine', action='store_true',
        dest='by_cosine', default=False, help='determine mapping by cosine')
    parser.add_option('--max_connections', type='int', dest='max_connections',
        default=None, help='Max number of topics a single topic can map to.', 
        metavar='NUM')
    return parser

def topicInnerProduct(tfidf1, tfidf2):
    inner_product = 0.0
    for word in tfidf1:
        if word in tfidf2:
            inner_product += float(tfidf1[word])*float(tfidf2[word])
    return inner_product

def topicCosineSimilarity(tfidf1, tfidf2):
    similarity = 0.0
    tfidf1_len = 0.0
    tfidf2_len = 0.0
    for term in tfidf1:
        tfidf1_len += float(tfidf1[term])*float(tfidf1[term])
        if term in tfidf2:
            similarity += float(tfidf1[term])*float(tfidf2[term])
    for term in tfidf2:
        tfidf2_len += float(tfidf2[term])*float(tfidf2[term])
    return similarity/(math.sqrt(tfidf1_len)*math.sqrt(tfidf2_len))

def topicDistance(tfidf1, tfidf2):
    sqr_distance = 0.0
    for term in tfidf1:
        p1 = float(tfidf1[term])
        if term not in tfidf2:
            sqr_distance += p1*p1
        else:
            p2 = float(tfidf2[term])
            sqr_distance += (p1-p2) * (p1-p2)
    for term in tfidf2:
        if term not in tfidf1:
            p2 = float(tfidf2[term])
            sqr_distance += p2*p2
    return math.sqrt(sqr_distance)

def getTopicMap(topicTFIDFs1, topicTFIDFs2, max_connections,
                by_distance, by_cosine):
    topic_map = [] 
    for tfidf1 in topicTFIDFs1:
        topic_vector = []
        for tfidf2 in topicTFIDFs2:
            if by_distance:
                similarity = 1.0/topicDistance(dict(tfidf1), dict(tfidf2))
            elif by_cosine:
                similarity = topicCosineSimilarity(dict(tfidf1), dict(tfidf2))
            else:
                similarity = topicInnerProduct(dict(tfidf1), dict(tfidf2))
            topic_vector.append(similarity)
        # if all similarities zero, then set all similarities to
        # 1.0/len(topic_vector)
        if np.linalg.norm(topic_vector, 1) == 0.0:
            topic_vector = [1.0/len(topic_vector) for x in topic_vector]
        if max_connections < len(topic_vector):
            # Limit number of connections
            queue = PriorityQueue()
            for idx in range(len(topic_vector)):
                similarity = topic_vector[idx]
                queue.put((similarity, idx))
                if queue.qsize() > max_connections:
                    (similarity, idx) = queue.get()
                    topic_vector[idx] = 0.0
        topic_map.append(topic_vector)
    return np.array(topic_map).transpose()

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicTFIDFs1.pickle topicTFIDFs2.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    topicTFIDFs1_fname = getAndCheckFilename(args[0])
    topicTFIDFs2_fname = getAndCheckFilename(args[1])

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topicTFIDFs1_fname
    topicTFIDFs1 = loadPickle(topicTFIDFs1_fname)

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topicTFIDFs2_fname
    topicTFIDFs2 = loadPickle(topicTFIDFs2_fname)

    # determine max connections
    if options.max_connections is not None:
        max_connections = options.max_connections
    else:
        max_connections = len(topicTFIDFs2)

    # get matrix mapping topics from space 1 to topics of space 2
    print 'Mapping topics between catalogues. . .'
    topic_map = getTopicMap(topicTFIDFs1, topicTFIDFs2, max_connections,
            options.by_distance, options.by_cosine)

    # dump tf-idfs
    print 'Saving topic map to %s. . .' % options.savefile
    pickle.dump(topic_map, open(options.savefile, 'w'))

    # print results
    if options.verbose:
        for i in range(len(topic_map)):
            print '  '.join('%.3f' % x for x in topic_map[i])

if __name__ == '__main__':
    main()
