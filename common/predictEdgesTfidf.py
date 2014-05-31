#!/usr/bin/env python

"""
Predicts the edges across two graphs using TF-IDF of item descriptions.
"""

from optparse import OptionParser
from collections import defaultdict
from stemming.porter2 import stem
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
    parser.add_option('-i', '--idfname', dest='idfname', default=None,
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords', default=None,
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--popgraph', dest='popgraph', default=None,
        help='Picked graph representing item "popularity".', metavar='FILE')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def TFIDFsimilarity(tfidf1, tfidf2, cosineSim=False):
    score = 0.0
    for word1 in tfidf1:
        if word1 in tfidf2:
            score += tfidf1[word1]*tfidf2[word1]
    if cosineSim:
        weight1 = sum([tfidf1[word]*tfidf1[word] for word in tfidf1])
        weight2 = sum([tfidf2[word]*tfidf2[word] for word in tfidf2])
        return (score / math.sqrt(weight1 * weight2))
    else:
        return score

def getTFIDFneighbors(queryTFIDF, itemTFIDFs, k, weights=None, cosineSim=False):
    queue = PriorityQueue() 
    for item in itemTFIDFs:
        similarity = TFIDFsimilarity(
            queryTFIDF, itemTFIDFs[item], cosineSim=cosineSim
        )
        if weights is not None:
            similarity *= weights[item]
        queue.put((similarity, item))
        if queue.qsize() > k:
            queue.get()
    neighbors = []
    while not queue.empty():
        (similarity, item) = queue.get()
        neighbors.append(item)
    return neighbors

def predictEdges(itemTFIDFs1, itemTFIDFs2, k, weights=None, cosineSim=False):
    predicted_edges = []
    count = 0
    for node1 in itemTFIDFs1:
        if count % displayInterval == 0:
            print 'Getting neighbors of %d / %d nodes' % (
                count, len(itemTFIDFs1.keys())
            )
        count += 1
        neighbors = getTFIDFneighbors(itemTFIDFs1[node1], itemTFIDFs2, k,
                                      weights=weights, cosineSim=cosineSim)
        predicted_edges += [(node1, n) for n in neighbors]
    return predicted_edges

def getItemTFs(db_conn, graph, stopwords=None, brandOnly=False):
    db_curs = db_conn.cursor()
    itemTFs = {}
    for item in graph:
        tf = defaultdict(int)
        db_curs.execute(selectDescriptionStmt, (item,))
        description = db_curs.fetchone()[0]
        # remove punctuation
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        # stem terms
        terms = [stem(term.lower()) for term in description.split()]
        for term in terms:
            if stopwords is not None and term in stopwords:
                continue
            tf[term] += 1
            # only consider first term in description if brandOnly=True
            if brandOnly:
                break
        itemTFs[item] = tf
    return itemTFs

def combineTFandIDF(itemTFs, termIDFs):
    """
    Get sparse TF-IDF vector for each topic by combining TFs with externally
    supplied IDFs.
    """
    itemTFIDFs = defaultdict(float)
    for item in itemTFs:
        itemTFIDFs[item] = dict(
            [(term, tf*termIDFs[term]) for (term, tf) in itemTFs[item].items()]
        )
    return itemTFIDFs

def main():
    # Parse options
    usage = 'Usage: %prog [options] database graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    dbFilename = getAndCheckFilename(args[0])
    graph1_filename = getAndCheckFilename(args[1])
    graph2_filename = getAndCheckFilename(args[2])

    # connect to database
    print 'Connecting to database %s. . .' % dbFilename
    db_conn = sqlite3.connect(dbFilename)

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)

    # get stop words
    print 'Loading Stopwords and IDFs. . .'
    stopwords = getStopwords(options.stopwords)

    # get TFs
    print 'Computing term frequencies. . .'
    itemTFs1 = getItemTFs(db_conn, graph1, stopwords=stopwords,
                          brandOnly=options.brandOnly)
    itemTFs2 = getItemTFs(db_conn, graph2, stopwords=stopwords,
                          brandOnly=options.brandOnly)

    # get TF-IDFs
    if options.idfname is not None:
        print 'Loading IDFs from %s. . .' % options.idfname
        termIDFs = loadPickle(options.idfname)
        itemTFIDFs1 = combineTFandIDF(itemTFs1, termIDFs)
        itemTFIDFs2 = combineTFandIDF(itemTFs2, termIDFs)
    else:
        itemTFIDFs1 = itemTFs1
        itemTFIDFs2 = itemTFs2

    # get popularity
    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph = loadPickle(options.popgraph)
        popDictionary = getPopDictionary(popgraph)
    else:
        popDictionary = None

    # predict edges
    print 'Predicting edges. . .'
    predicted_edges = predictEdges(
        itemTFIDFs1,
        itemTFIDFs2,
        options.k,
        weights=popDictionary,
        cosineSim=options.cosine
    )

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
