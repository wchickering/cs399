#!/usr/bin/env python

"""
Predicts the edges between graph 1 and graph 2 based on LDA model.
"""

from optparse import OptionParser
import pickle
import os
import sys
import sqlite3
import LDA_util
import random
import numpy as np
from Queue import PriorityQueue
#import KNNSearchEngine

# params
displayInterval = 1

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', '--kPredictions', dest='k', default='10',
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('--graph1', dest='graph1_filename', 
        default='data/graph1.pickle', 
        help='Pickle storing graph 1', metavar='FILE')
    parser.add_option('--graph2', dest='graph2_filename', 
        default='data/graph2.pickle', 
        help='Pickle storing graph 2', metavar='FILE')
    parser.add_option('--lda1', dest='lda1_filename', 
        default='data/lda1.pickle', 
        help='Pickle storing lda model for graph 1', metavar='FILE')
    parser.add_option('--lda2', dest='lda2_filename', 
        default='data/lda2.pickle', 
        help='Pickle storing lda model for graph 2', metavar='FILE')
    parser.add_option('--topicmap', dest='topic_map_filename', 
        default='data/topicMap.pickle', 
        help='Pickle storing topic map from topci in graph1 to topics in graph 2',
        metavar='FILE')
    parser.add_option('-o', '--output', dest='predicted_edges_filename',
        default='data/predicted_edges.pickle',
        help='Pickle to dump predicted edges', metavar='OUT_FILE')
    parser.add_option('-r', '--random', 
        action='store_true', dest='randomPredict', default=False,
        help='make random predictions')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def getTopicsFromModel(lda, node):
    return LDA_util.getTopicGivenItemProbs(lda)[:, lda.id2word.token2id[str(node)]]

def getTopicsFromSpace(topic_space, lda, node):
    lda.id2word.token2id[str(node)]
    return topic_space[:, lda.id2word.token2id[str(node)]]

def transformTopics(topics, topic_map):
    topic_map = np.array(topic_map)
    topics = np.array(topics)
    return np.dot(topic_map, topics)

def getDistance(point1, point2):
    point1 = np.array(point1)
    point2 = np.array(point2)
    return np.linalg.norm(point2 - point1)

def getNeighbors(graph, lda, node_topics, k):
    # get top k nearest neighbors by L2 distance in topic space 2
    queue = PriorityQueue() # priority queue makes this nlogk
    for node2 in graph:
        node_topics2 = getTopicsFromModel(lda, node2) 
        distance = getDistance(node_topics, node_topics2)
        queue.put((-distance, node2))
        if queue.qsize() > k:
            queue.get()
    neighbors = []
    while not queue.empty():
        (distance, node2) = queue.get()
        neighbors.append(node2)
    return neighbors

#def kNN(engine, node_topics, k):
#    (distances, neighbors) = engine.kneighbors(node_topics, k)
#    return neighbors

def transformTopicSpace(lda1, topic_map):
    lda1_matrix = LDA_util.getTopicGivenItemProbs(lda1)
    return np.dot(topic_map, lda1_matrix)

def predictEdges(graph1, graph2, k, lda1, lda2, topic_map, topic_space):
        #topic_space, engine):
    predicted_edges = []
    count = 0
    for node in graph1:
        if count % displayInterval == 0:
            print 'Predicted edges nodes for %d / %d nodes of graph1'\
                % (count, len(graph1))
        count += 1
        # get topic space 2 representation of node in graph1
        node_topics2 = getTopicsFromSpace(topic_space, lda1, node)
        # find the k nearest neighbors in graph2 to that topic space
        neighbors = getNeighbors(graph2, lda2, node_topics2, k)
        #neighbors = kNN(engine, node_topics2)
        for neighbor in neighbors:
            predicted_edges.append((node, neighbor))
    return predicted_edges

def predictRandomEdges(graph1, graph2, k):
    predicted_edges = []
    # get the items in graph2 that are in the right category
    for item in graph1:
        # pick k of them randomly and guess those edges
        for i in range(k):
            item2 = random.choice(graph2.keys())
            predicted_edges.append((item, item2))
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # load graphs, models, and map
    print 'Load pickles. .'
    if not os.path.isfile(options.graph1_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % graph1_filename
    graph1 = loadPickle(options.graph1_filename)
    if not os.path.isfile(options.graph2_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % graph2_filename
    graph2 = loadPickle(options.graph2_filename)
    if not os.path.isfile(options.lda1_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % lda1_filename
    lda1 = loadPickle(options.lda1_filename)
    if not os.path.isfile(options.lda2_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % lda2_filename
    lda2 = loadPickle(options.lda2_filename)
    if not os.path.isfile(options.topic_map_filename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % topic_map_filename
    topic_map = loadPickle(options.topic_map_filename)

    print 'Transform topic space 1 to topic space 2. .'
    transformed_space = transformTopicSpace(lda1, topic_map)

    #print 'Create KNN search engine. .'
    #data = LDA_util.getTopicGivenItemProbs(lda2).transpose()
    #dictionary = lda2.id2word
    #searchEngine = KNNSearchEngine(data, dictionary)

    # predict edges
    if options.randomPredict:
        print 'Randomly predict edges. .'
        predicted_edges = predictRandomEdges(graph1, graph2, int(options.k))
    else:
        print 'Predict edges. .'
        predicted_edges = predictEdges(graph1, graph2, int(options.k), lda1,
                lda2, topic_map, transformed_space)
    #           categories, lda1, lda2, topic_map, transformed_space, searchEngine)
    
    print 'Dump results. .'
    # dump results
    pickle.dump(predicted_edges, open(options.predicted_edges_filename, 'w'))

if __name__ == '__main__':
    main()
