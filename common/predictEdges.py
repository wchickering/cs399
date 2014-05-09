#!/usr/bin/env python

"""
Predicts the edges across two LDA/LSI model.
"""

from stemming.porter2 import stem
from optparse import OptionParser
from collections import defaultdict
from Queue import PriorityQueue
import pickle
import os
import sys
import random
import sqlite3
import string
import numpy as np

# local modules
import LDA_util as lda
import LSI_util as lsi
from KNNSearchEngine import KNNSearchEngine

selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'
displayInterval = 100

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('-r', '--random', action='store_true', dest='random',
        default=False, help='Make random predictions.')
    parser.add_option('--tfidf', action='store_true', dest='tfidf_compare',
        default=False, help='Make predictions based on item-item tfidf similarity.')
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Database to pull descriptions from.')
    parser.add_option('-i', '--idfname', dest='idfname',
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords',
        default='data/stopwords.txt',
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        obj = pickle.load(f)
    return obj

def loadModel(filename):
    if filename.endswith('.pickle'):
        # load LDA model
        model = loadPickle(filename)
        dictionary = {}
        for i, node in model.id2word.items():
            dictionary[i] = int(node)
        data = lda.getTopicGivenItemProbs(model)
    elif filename.endswith('.npz'):
        # load LSI model
        npzfile = np.load(filename)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        nodes = npzfile['dictionary']
        dictionary = {}
        for i in range(len(nodes)):
            dictionary[i] = int(nodes[i])
        data = lsi.getTermConcepts(u, s)
    else:
        print >> sys.stderr,\
            'error: Model file must be either a .pickle or .npz file.'
        return None
    return data, dictionary

def predictEdges(topic_space, dictionary, k, searchEngine):
    predicted_edges = []
    for index, node in dictionary.items():
        distances, neighbors = searchEngine.kneighbors(topic_space[:, index], k)
        predicted_edges += [(int(node), int(neighbor))\
                            for neighbor in neighbors[0]]
    return predicted_edges

def tfidfSimilarity(tfidf1, tfidf2):
    score = 0.0
    for word1 in tfidf1:
        if word1 in tfidf2:
            score += tfidf1[word1]*tfidf2[word1]
    return score

def tfidfNeighbors(tfidf1, tfidfs2, k):
    queue = PriorityQueue() # priority queue makes this nlogk
    for node2 in tfidfs2:
        similarity = tfidfSimilarity(tfidf1, tfidfs2[node2])
        queue.put((similarity, node2))
        if queue.qsize() > k:
            queue.get()
    neighbors = []
    while not queue.empty():
        (similarity, node2) = queue.get()
        neighbors.append(node2)
    return neighbors

def calculateTfidfs(db_conn, dictionary, idf, stopwords=None):
    db_curs = db_conn.cursor()
    tfidfs = {}
    for item in dictionary:
        tfidf = defaultdict(float)
        db_curs.execute(selectDescriptionStmt, (dictionary[item],))
        description = db_curs.fetchone()[0]
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        words = [stem(w.lower()) for w in description.split()]
        for word in words:
            if stopwords is not None and word in stopwords:
                continue
            tfidf[word] += idf[word]
        tfidfs[dictionary[item]] = tfidf
    return tfidfs

def predictTfidfEdges(db_conn, dictionary1, dictionary2, k, idf, stopwords=None):
    predicted_edges = []
    tfidfs1 = calculateTfidfs(db_conn, dictionary1, idf, stopwords=stopwords)
    tfidfs2 = calculateTfidfs(db_conn, dictionary2, idf, stopwords=stopwords)
    count = 0
    for node1 in tfidfs1:
        if count % displayInterval == 0:
            print 'Getting neighbors of %d / %d nodes' % (count, len(tfidfs1.keys()))
        count += 1
        neighbors = tfidfNeighbors(tfidfs1[node1], tfidfs2, k)
        predicted_edges += [(node1, n) for n in neighbors]
    return predicted_edges

def predictRandomEdges(dictionary1, dictionary2, k):
    predicted_edges = []
    for node1 in dictionary1:
        # pick k items randomly and guess those edges
        for i in range(k):
            node2 = random.choice(dictionary2.keys())
            predicted_edges.append((dictionary1[node1], 
                dictionary2[node2]))
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicMap.pickle modelfile1 modelfile2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    topic_map_filename = args[0]
    if not os.path.isfile(topic_map_filename):
        parser.error('Cannot find %s' % topic_map_filename)
    model1_filename = args[1]
    if not os.path.isfile(model1_filename):
        parser.error('Cannot find %s' % model1_filename)
    model2_filename = args[2]
    if not os.path.isfile(model2_filename):
        parser.error('Cannot find %s' % model2_filename)

    # load topic map
    print 'Loading topic map from %s. . .' % topic_map_filename
    topic_map = loadPickle(topic_map_filename)

    # load models
    print 'Loading model1 from %s. . .' % model1_filename
    data1, dictionary1 = loadModel(model1_filename)
    print 'Loading model2 from %s. . .' % model2_filename
    data2, dictionary2 = loadModel(model2_filename)

    # transform to common topic space
    print 'Transforming topic space 1 to topic space 2. . .'
    transformed_space = np.dot(topic_map, data1)

    # create search engine
    print 'Creating KNN search engine from model2. . .'
    searchEngine = KNNSearchEngine(data2.transpose(), dictionary2)

    # predict edges
    if options.random:
        print 'Randomly predicting edges. . .'
        predicted_edges = predictRandomEdges(dictionary1, dictionary2,
                                             options.k)
    elif options.tfidf_compare:
        print 'Predicting edges by item-item tfidf similarity. .'
        print 'Loading Stopwords and IDFs. . .'
        # get stop words
        if os.path.isfile(options.stopwords):
            with open(options.stopwords, 'r') as f:
                try:
                    stopwords = f.readline().split(',')
                except:
                    print >> sys.stderr, 'Failed to parse stop words.'
                    return
        else:
            print >> sys.stderr,\
                'WARNING: stop words file not found: %s' % options.stopwords
            stopwords = None

        with open(options.idfname, 'r') as f:
            idf = pickle.load(f)
        print 'Connecting to database. .'
        db_conn = sqlite3.connect(options.dbname)
        predicted_edges = predictTfidfEdges(db_conn, dictionary1, dictionary2,
                                            options.k, idf, stopwords=stopwords)
    else:
        print 'Predicting edges. . .'
        predicted_edges = predictEdges(transformed_space, dictionary1,
                                       options.k, searchEngine)
    
    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
