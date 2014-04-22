#!/usr/bin/env python

"""
Maps one topic space to another using TF-IDF vector representations of each
topic and comparing each. The outup is a matrix with unit length columns by the
L1 norm. Multiplying this matrix by a topic column vector of catalogue 2 gives a
topic vector in catalogue 1's space.
"""

from stemming.porter2 import stem
from optparse import OptionParser
from collections import defaultdict
import pickle
import os
import sys
import sqlite3
import string
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/topic_map.db',
        help='Name of pickle to write topic map to.', metavar='FILE')
    parser.add_option('-n', '--topnwords', type=int, dest='topnwords', 
        default=1000, help='Number of top words in tfidf to compare.',
        metavar='NUM')
    return parser

def topicTopicSim(topic1, topic2):
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

def transformMatrix(matrix):
    matrix_t = [[0 for x in xrange(len(matrix))] for x in xrange(len(matrix[0]))]
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix_t[j][i] = matrix[i][j]
    return matrix_t

def getTopicMap(tfidf1, tfidf2):
    topic_map = [] # Transform from space 2 to space 1
    for topic2 in tfidf2:
        # Represent topic in space 1
        topic_vector = []
        for topic1 in tfidf1:
             topic_vector.append(topicTopicSim(topic2, topic1))
        # Normalize vector and add to topic map
        topic_map.append(topic_vector/np.linalg.norm(topic_vector, 1))
    return transformMatrix(topic_map)

def main():
    # Parse options
    usage = 'Usage: %prog [options] <tfidf1.pickle> <tfidf2.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    tfidfname1 = args[0]
    tfidfname2 = args[1]
    if not os.path.isfile(tfidfname1):
        print >> sys.stderr, 'Cannot find %s' % tfidfname1
        return
    if not os.path.isfile(tfidfname2):
        print >> sys.stderr, 'Cannot find %s' % tfidfname2
        return

    # load tfidf1 pickle
    print 'Load tfidf pickle of first catalogue. .'
    with open(tfidfname1, 'r') as f:
        tfidf1 = pickle.load(f)

    # load tfidf2 pickle
    print 'Load tfidf pickle of second catalogue. .'
    with open(tfidfname2, 'r') as f:
        tfidf2 = pickle.load(f)

    # truncate to get top tfidfs in each topic
    for topic in range(len(tfidf1)):
        tfidf1[topic] = np.array(tfidf1[topic])
        tfidf1[topic] = tfidf1[topic][0:options.topnwords, :]
    for topic in range(len(tfidf2)):
        tfidf2[topic] = np.array(tfidf2[topic])
        tfidf2[topic] = tfidf2[topic][0:options.topnwords, :]
        
    # sort each topic of tfidfs by word alphabetically
    print 'Sort tfidf topics by word. .'
    for topic in range(len(tfidf1)):
        ind = np.argsort(tfidf1[topic][:,0])
        tfidf1[topic] = tfidf1[topic][ind, :]
    for topic in range(len(tfidf2)):
        ind = np.argsort(tfidf2[topic][:,0])
        tfidf2[topic] = tfidf2[topic][ind, :]

    # get matrix mapping topics from space 2 to topics of space 1
    print 'Map topics from first catalogue to topics of second catalogue. .'
    topic_map = getTopicMap(tfidf1, tfidf2)

    # dump tf-idfs
    pickle.dump(topic_map, open(options.outputpickle, 'w'))

    # print results
    for i in range(len(topic_map)):
        print '  '.join('%.3f' % x for x in topic_map[i])

if __name__ == '__main__':
    main()
