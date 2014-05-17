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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/topic_map.pickle',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-n', '--topnwords', type=int, dest='topnwords', 
        default=1000, help='Number of top words per topic to compare.',
        metavar='NUM')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='Print top words')
    parser.add_option('-d', '--by_distance', action='store_true',
        dest='by_distance', default=False, help='determine mapping by distance')
    parser.add_option('--max_connections', type='int', dest='max_connections',
        default=1000, help='Max number of topics a single topic can map to.', 
        metavar='NUM')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        obj = pickle.load(f)
    return obj

def topicSimilarity(topic1, topic2):
    similarity = 0.0
    # Traverse ordered lists of words for matches
    i = 0
    j = 0
    while i < len(topic1) and j < len(topic2):
        word1 = topic1[i][0]
        word2 = topic2[j][0]
        if word1 == word2:
            similarity += float(topic1[i][1]) * float(topic2[j][1])
            i += 1
            j += 1
        elif word1 < word2:
            i += 1
        else:
            j += 1
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

def transformMatrix(matrix):
    matrix_t = [[0 for x in xrange(len(matrix))] for x in xrange(len(matrix[0]))]
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix_t[j][i] = matrix[i][j]
    return matrix_t

def getTopicMap(topics1, topics2, max_connections, by_distance):
    topic_map = [] 
    for topic1 in topics1:
        topic_vector = []
        for topic2 in topics2:
            if by_distance:
                similarity = 1.0/topicDistance(dict(topic1), dict(topic2))
            else:
                similarity = topicSimilarity(topic1, topic2)
            topic_vector.append(similarity)
        # Limit number of connections
        queue = PriorityQueue() 
        for idx in range(len(topic_vector)):
            similarity = topic_vector[idx]
            queue.put((similarity, idx))
            if queue.qsize() > max_connections:
                (similarity, idx) = queue.get()
                topic_vector[idx] = 0.0
        topic_map.append(topic_vector/np.linalg.norm(topic_vector, 1))
    return transformMatrix(topic_map)

def truncateTopics(topics, topnwords):
    for topic in range(len(topics)):
        topics[topic] = np.array(topics[topic])
        topics[topic] = topics[topic][0:topnwords, :]
    return topics

def main():
    # Parse options
    usage = 'Usage: %prog [options] <topics1.pickle> <topics2.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    topics1_fname = args[0]
    topics2_fname = args[1]
    if not os.path.isfile(topics1_fname):
        print >> sys.stderr, 'error: Cannot find %s' % topics1_fname
        return
    if not os.path.isfile(topics2_fname):
        print >> sys.stderr, 'error: Cannot find %s' % topics2_fname
        return

        # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topics1_fname
    topics1 = loadPickle(topics1_fname)

    # load topics pickle
    print 'Loading topics of first catalogue from %s. . .' % topics2_fname
    topics2 = loadPickle(topics2_fname)

    # truncate to get top words in each topic
    topics1 = truncateTopics(topics1, options.topnwords)
    topics2 = truncateTopics(topics2, options.topnwords)

    # sort each topic by word alphabetically
    print 'Sorting topics by word. . .'
    for topic in range(len(topics1)):
        ind = np.argsort(topics1[topic][:,0])
        topics1[topic] = topics1[topic][ind, :]
    for topic in range(len(topics2)):
        ind = np.argsort(topics2[topic][:,0])
        topics2[topic] = topics2[topic][ind, :]
        
    # get matrix mapping topics from space 1 to topics of space 2
    print 'Mapping topics between catalogues. . .'
    topic_map = getTopicMap(topics1, topics2, options.max_connections,
            options.by_distance)

    # assert that all columns add up to 1
    assert(np.array(topic_map).sum(axis=0).all() == 
            np.ones((len(topic_map), 1)).all())

    # dump tf-idfs
    print 'Saving topic map to %s. . .' % options.outputpickle
    pickle.dump(topic_map, open(options.outputpickle, 'w'))

    # print results
    if options.verbose:
        for i in range(len(topic_map)):
            print '  '.join('%.3f' % x for x in topic_map[i])

if __name__ == '__main__':
    main()
