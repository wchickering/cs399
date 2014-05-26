#!/usr/bin/env python

"""
Predicts the edges across two graphs using tfidf of descriptions.
"""

from stemming.porter2 import stem
from optparse import OptionParser
from collections import defaultdict
from Queue import PriorityQueue
import pickle
import os
import sys
import sqlite3
import string
import math

# local modules
from Util import loadPickle, getAndCheckFilename, getStopwords
from Prediction_util import getPopDictionary

# params
selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'
displayInterval = 100

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--cosine', action='store_true', dest='cosine',
        default=False,
        help='Make predictions based on item-item tfidf similarity.')
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Database to pull descriptions from.')
    parser.add_option('-i', '--idfname', dest='idfname',
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords',
        default='data/stopwords.txt',
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--popgraph', dest='popgraph', default=None,
        help='Picked graph representing item "popularity".', metavar='FILE')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def tfidfSimilarity(tfidf1, tfidf2, cosine):
    score = 0.0
    for word1 in tfidf1:
        if word1 in tfidf2:
            score += tfidf1[word1]*tfidf2[word1]
    if cosine:
        weight1 = sum([tfidf1[word]*tfidf1[word] for word in tfidf1])
        weight2 = sum([tfidf2[word]*tfidf2[word] for word in tfidf2])
        return (score / math.sqrt(weight1 * weight2))
    else:
        return score

def tfidfNeighbors(tfidf1, tfidfs2, k, cosine, popDictionary):
    queue = PriorityQueue() 
    for node2 in tfidfs2:
        similarity = tfidfSimilarity(tfidf1, tfidfs2[node2], cosine)
        if popDictionary is not None:
            similarity *= popDictionary[node2]
        queue.put((similarity, node2))
        if queue.qsize() > k:
            queue.get()
    neighbors = []
    while not queue.empty():
        (similarity, node2) = queue.get()
        neighbors.append(node2)
    return neighbors

def predictEdges(tfidfs1, tfidfs2, k, cosine, popDictionary):
    predicted_edges = []
    count = 0
    for node1 in tfidfs1:
        if count % displayInterval == 0:
            print 'Getting neighbors of %d / %d nodes' % (count, len(tfidfs1.keys()))
        count += 1
        neighbors = tfidfNeighbors(tfidfs1[node1], tfidfs2, k, cosine,
                popDictionary)
        predicted_edges += [(node1, n) for n in neighbors]
    return predicted_edges

def calculateTfidfs(db_conn, graph, idf, stopwords=None, brandOnly=False):
    db_curs = db_conn.cursor()
    tfidfs = {}
    for item in graph:
        tfidf = defaultdict(float)
        db_curs.execute(selectDescriptionStmt, (item,))
        description = db_curs.fetchone()[0]
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        words = [stem(w.lower()) for w in description.split()]
        for word in words:
            if stopwords is not None and word in stopwords:
                continue
            tfidf[word] += idf[word]
            if brandOnly:
                break
        tfidfs[item] = tfidf
    return tfidfs

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments') 

    graph1_filename = getAndCheckFilename(args[0])
    graph2_filename = getAndCheckFilename(args[1])
    idf_filename = getAndCheckFilename(options.idfname)

    # get stop words
    print 'Loading Stopwords and IDFs. . .'
    stopwords = getStopwords(options.stopwords)

    # Get popularity
    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph_fname = getAndCheckFilename(options.popgraph)
        popgraph = loadPickle(popgraph_fname)
        popDictionary = getPopDictionary(popgraph)
    else:
        popDictionary = None

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)
    print 'Loading idfs from %s. . .' % idf_filename
    idf = loadPickle(idf_filename)

    # connect to database
    print 'Connecting to database. .'
    db_conn = sqlite3.connect(options.dbname)

    # calculate tfidfs for words of items in each graph
    print 'Calculating tfidfs. .'
    tfidfs1 = calculateTfidfs(db_conn, graph1, idf, stopwords=stopwords,
                              brandOnly=options.brandOnly)
    tfidfs2 = calculateTfidfs(db_conn, graph2, idf, stopwords=stopwords,
                              brandOnly=options.brandOnly)

    # predict edges
    print 'Predicting edges. .'
    predicted_edges = predictEdges(tfidfs1, tfidfs2, options.k,
            options.cosine, popDictionary=popDictionary)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
