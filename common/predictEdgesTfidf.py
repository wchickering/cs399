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

# db params
selectDescriptionStmt =\
    ('SELECT Description '
     'FROM Products '
     'WHERE Id = :Id')
selectShortDescriptionStmt =\
    ('SELECT ShortDescription '
     'FROM Products '
     'WHERE Id = :Id')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='float', dest='k', default=2.0,
        help='Number of predicted edges per node.', metavar='FLOAT')
    parser.add_option('--symmetric', action='store_true', dest='symmetric',
        default=False,
        help=('Predict k edges for each node in each graph connecting to a '
              'node in the other graph.'))
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
    parser.add_option('--short-only', action='store_true', dest='shortOnly',
        default=False, help='Limit text to that in short descriptions.')
    parser.add_option('--bigrams', action='store_true', dest='bigrams',
        default=False, help='Include bigrams as well as unigrams.')
    parser.add_option('--popdict', dest='popdict', default=None,
        help='Picked popularity dictionary.', metavar='FILE')
    parser.add_option('--min-pop', type='float', dest='minPop',
        default=0.0, help='Minimum popularity to be included in search engine.',
        metavar='FLOAT')
    parser.add_option('--weight-in', action='store_true', dest='weightIn',
        default=False,
        help='Weight KNN search engine results using popDictionary.')
    parser.add_option('--weight-out', action='store_true', dest='weightOut',
        default=False,
        help='Weight choice of outgoing edges using popDictionary.')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def getItemTFs(db_conn, graph, stopwords=None, shortOnly=False, bigrams=False,
               brandOnly=False):
    db_curs = db_conn.cursor()
    itemTFs = {}
    for item in graph:
        tf = defaultdict(int)
        if shortOnly:
            db_curs.execute(selectShortDescriptionStmt, (item,))
        else:
            db_curs.execute(selectDescriptionStmt, (item,))
        row = db_curs.fetchone()
        description = row[0]
        # remove punctuation
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        # stem terms
        terms = [stem(term.lower()) for term in description.split()]
        lastTerm = None
        for term in terms:
            # skip stopwords
            if stopwords is not None and term in stopwords:
                continue
            tf[term] += 1
            if bigrams and lastTerm is not None:
                bg = ' '.join([lastTerm, term])
                tf[bg] += 1
            lastTerm = term
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

def getTFIDFneighbors(queryTFIDF, itemTFIDFs, k, weights=None, minWeight=0,
                      cosineSim=False):
    queue = PriorityQueue()
    for item in itemTFIDFs:
        if weights is not None and minWeight > 0:
            if weights[item] < minWeight:
                continue
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

def predictEdges(itemTFIDFs1, itemTFIDFs2, k, symmetric=False, weights=None,
                 weightIn=True, weightOut=False, minWeight=0, cosineSim=False):
    predictedEdges = []
    if weights is not None and weightOut:
        print 'Predicting edges (weighted outgoing). . . '
        totalPredictions = int(len(itemTFIDFs1)*k)
        if symmetric:
            totalPredictions += int(len(itemTFIDFs2)*k)
        totalPopularity = 0.0
        for item1 in itemTFIDFs1:
            totalPopularity += weights[item1]
        if symmetric:
            for item2 in itemTFIDFs2:
                totalPopularity += weights[item2]
        for item1 in itemTFIDFs1:
            numPredictions = int(round(totalPredictions*\
                                        weights[item1]/\
                                        totalPopularity))
            if numPredictions > 0:
                neighbors = getTFIDFneighbors(
                    itemTFIDFs1[item1],
                    itemTFIDFs2,
                    numPredictions,
                    weights=weights if weightIn else None,
                    minWeight=minWeight,
                    cosineSim=cosineSim
                )
                predictedEdges += [(item1, n) for n in neighbors]
        if symmetric:
            for item2 in itemTFIDFs2:
                numPredictions = int(round(totalPredictions*\
                                            weights[item2]/\
                                            totalPopularity))
                if numPredictions > 0:
                    neighbors = getTFIDFneighbors(
                        itemTFIDFs2[item2],
                        itemTFIDFs1,
                        numPredictions,
                        weights=weights if weightIn else None,
                        minWeight=minWeight,
                        cosineSim=cosineSim
                    )
                    predictedEdges += [(item2, n) for n in neighbors]
    else:
        print 'Predicting edges (uniform outgoing). . .'
        for item1 in itemTFIDFs1:
            neighbors = getTFIDFneighbors(
                itemTFIDFs1[item1],
                itemTFIDFs2,
                k,
                weights=weights if weightIn else None,
                minWeight=minWeight,
                cosineSim=cosineSim
            )
            predictedEdges += [(item1, n) for n in neighbors]
        if symmetric:
            for item2 in itemTFIDFs2:
                neighbors = getTFIDFneighbors(
                    itemTFIDFs2[item2],
                    itemTFIDFs1,
                    k,
                    weights=weights if weightIn else None,
                    minWeight=minWeight,
                    cosineSim=cosineSim
                )
                predictedEdges += [(item2, n) for n in neighbors]
    return predictedEdges

def main():
    # Parse options
    usage = 'Usage: %prog [options] database graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    dbFilename = getAndCheckFilename(args[0])
    graphFilename1 = getAndCheckFilename(args[1])
    graphFilename2 = getAndCheckFilename(args[2])

    # connect to database
    print 'Connecting to database %s. . .' % dbFilename
    db_conn = sqlite3.connect(dbFilename)

    # load graphs
    print 'Loading graph1 from %s. . .' % graphFilename1
    graph1 = loadPickle(graphFilename1)
    print 'Loading graph2 from %s. . .' % graphFilename2
    graph2 = loadPickle(graphFilename2)

    # get stop words
    print 'Loading Stopwords and IDFs. . .'
    stopwords = getStopwords(options.stopwords)

    # get TFs
    print 'Computing term frequencies. . .'
    itemTFs1 = getItemTFs(db_conn, graph1, stopwords=stopwords,
                          shortOnly=options.shortOnly, bigrams=options.bigrams,
                          brandOnly=options.brandOnly)
    itemTFs2 = getItemTFs(db_conn, graph2, stopwords=stopwords,
                          shortOnly=options.shortOnly, bigrams=options.bigrams,
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
    if options.popdict:
        print 'Loading popularity dictionary from %s. . .' % options.popdict
        popDictionary = loadPickle(options.popdict)
    else:
        popDictionary = None

    # predict edges
    predictedEdges = predictEdges(
        itemTFIDFs1,
        itemTFIDFs2,
        options.k,
        symmetric=options.symmetric,
        weights=popDictionary,
        weightIn=options.weightIn,
        weightOut=options.weightOut,
        minWeight=options.minPop,
        cosineSim=options.cosine
    )

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predictedEdges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
