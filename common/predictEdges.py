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
import numpy as np
from Queue import PriorityQueue

# params
displayInterval = 1000

# db_params
selectCategories =\
   ('SELECT Id, Category FROM Categories;')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', '--kPredictions', dest='k', default='10',
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('-d', '--database', dest='dbname', default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-c', '--category', dest='category', default=None,
        help='Category to confine predictions to.', metavar='CAT')
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
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def genCategoryMap(db_curs):
    categories = {}
    product_ids = db_curs.execute(selectCategories)
    for (product_id, category) in product_ids:
        categories[product_id] = category
    return categories

def getTopics(lda, node):
    return LDA_util.getTopicGivenItemProbs(lda)[:, lda.id2word.token2id[str(node)]]

def transformTopics(topics, topic_map):
    topic_map = np.array(topic_map)
    topics = np.array(topics)
    return np.dot(topic_map, topics)

def getDistance(point1, point2):
    point1 = np.array(point1)
    point2 = np.array(point2)
    return np.linalg.norm(point2 - point1)

def getNeighbors(graph, lda, node_topics, k, category, categories):
    # get top k nearest neighbors by L2 distance in topic space 2
    queue = PriorityQueue() # priority queue makes this nlogk
    for node2 in graph:
        if categories[node2] != category:
            continue
        node_topics2 = getTopics(lda, node2) 
        distance = getDistance(node_topics, node_topics2)
        queue.put((-distance, node2))
        if queue.qsize() > k:
            queue.get()
    neighbors = []
    while not queue.empty():
        (distance, node2) = queue.get()
        neighbors.append(node2)
    return neighbors

def predictEdges(graph1, graph2, k, category, categories, lda1, lda2, topic_map):
    predicted_edges = []
    count = 0
    for node in graph1:
        if count % displayInterval == 0:
            print 'Predicted edges or skipped nodes for %d / %d nodes of graph1'\
                % (count, len(graph1))
        count += 1
        if categories[node] != category:
            continue
        # represent this node in graph1 topic space
        node_topics1 = getTopics(lda1, node)
        # convert that to graph2 topic space
        node_topics2 = transformTopics(node_topics1, topic_map)
        # find the k nearest neighbors in graph2 to that topic space
        neighbors = getNeighbors(graph2, lda2, node_topics2, k, category,
                categories)
        for neighbor in neighbors:
            predicted_edges.append((node, neighbor))
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

    print 'Generate category map from database. .'
    # generate category map
    db_conn = sqlite3.connect(options.dbname)
    db_curs = db_conn.cursor()
    categories = genCategoryMap(db_curs)

    print 'Predict edges. .'
    # predict edges
    predicted_edges = predictEdges(graph1, graph2, int(options.k), options.category,
            categories, lda1, lda2, topic_map)
    
    print 'Dump results. .'
    # dump results
    pickle.dump(predicted_edges, open(options.predicted_edges_filename, 'w'))

if __name__ == '__main__':
    main()
