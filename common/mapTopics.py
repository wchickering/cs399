#!/usr/bin/env python

"""
Maps one topic space to another using TF-IDF vector representations of each
topic and comparing each. The outup is a matrix with unit length columns by the
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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile',
        default='data/topic_map.pickle',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Print top words')
    parser.add_option('-d', '--by_distance', action='store_true',
        dest='by_distance', default=False, help='determine mapping by distance')
    parser.add_option('--max_connections', type='int', dest='max_connections',
        default=1000, help='Max number of topics a single topic can map to.', 
        metavar='NUM')
    return parser

def topicSimilarity(topic1, topic2):
    similarity = 0.0
    for word in topic1:
        if word in topic2:
            similarity += float(topic1[word])*float(topic2[word])
    return similarity

def topicDistance(topic1, topic2):
    sqr_distance = 0.0
    for word in topic1:
        p1 = float(topic1[word])
        if word not in topic2:
            sqr_distance += p1*p1
        else:
            p2 = float(topic2[word])
            sqr_distance += (p1-p2) * (p1-p2)
    for word in topic2:
        if word not in topic1:
            p2 = float(topic2[word])
            sqr_distance += p2*p2
    return math.sqrt(sqr_distance)

def getTopicMap(topics1, topics2, max_connections, by_distance):
    topic_map = [] 
    for topic1 in topics1:
        topic_vector = []
        for topic2 in topics2:
            if by_distance:
                similarity = 1.0/topicDistance(dict(topic1), dict(topic2))
            else:
                similarity = topicSimilarity(dict(topic1), dict(topic2))
            topic_vector.append(similarity)
        # if all similarities zero, then set all similarities to 1.0
        if np.linalg.norm(topic_vector, 1) == 0.0:
            topic_vector = [1.0 for x in topic_vector]
        # Limit number of connections
        queue = PriorityQueue() 
        for idx in range(len(topic_vector)):
            similarity = topic_vector[idx]
            queue.put((similarity, idx))
            if queue.qsize() > max_connections:
                (similarity, idx) = queue.get()
                topic_vector[idx] = 0.0
        #topic_map.append(topic_vector/np.linalg.norm(topic_vector, 0))
        topic_map.append(topic_vector)
    return np.array(topic_map).transpose()

def main():
    # Parse options
    usage = 'Usage: %prog [options] <topics1.pickle topics2.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    topics1_fname = getAndCheckFilename(args[0])
    topics2_fname = getAndCheckFilename(args[1])

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topics1_fname
    topics1 = loadPickle(topics1_fname)

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topics2_fname
    topics2 = loadPickle(topics2_fname)

    # get matrix mapping topics from space 1 to topics of space 2
    print 'Mapping topics between catalogues. . .'
    topic_map = getTopicMap(topics1, topics2, options.max_connections,
            options.by_distance)

    # dump tf-idfs
    print 'Saving topic map to %s. . .' % options.savefile
    pickle.dump(topic_map, open(options.savefile, 'w'))

    # print results
    if options.verbose:
        for i in range(len(topic_map)):
            print '  '.join('%.3f' % x for x in topic_map[i])

if __name__ == '__main__':
    main()
