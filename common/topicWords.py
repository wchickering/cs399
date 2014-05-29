#!/usr/bin/env python

"""
Compute a sparse TF-IDF vectors for each topic/concept of an LDA/LSI model.
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
import math

# local modules
from Util import loadPickle, getAndCheckFilename, getStopwords
from LSI_util import showConcept

# db params
selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-i', '--idfname', dest='idfname', default=None,
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=100,
        help='Number of items per topic to consider.', metavar='NUM')
    parser.add_option('-k', '--topnPrint', type='int', dest='topnPrint',
        default=10, help='Number of words per topic to print.', metavar='NUM')
    parser.add_option('-v', '--verbose', 
        action='store_true', dest='verbose', default=False,
        help='Print top words')
    parser.add_option('--savefile', dest='savefile', default='tfidf.pickle',
        help='Name of pickle to save tfidfs per topic.', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords', default=None,
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def getTopicTFs(db_conn, topicDists, stopwords=None, brandOnly=False):
    db_curs = db_conn.cursor()
    topicTFs = []
    for topic in range(len(topicDists)):
        tf = defaultdict(float)
        for i in range(len(topicDists[topic])):
            topicStrength = topicDists[topic][i][0]
            item = topicDists[topic][i][1]
            db_curs.execute(selectDescriptionStmt, (item,))
            description = db_curs.fetchone()[0]
            # Remove punctuation
            description = ''.join(ch for ch in description\
                                  if ch not in string.punctuation)
            # Stem terms
            terms = [stem(term.lower()) for term in description.split()]
            for term in terms:
                # Skip stopwords
                if stopwords is not None and term in stopwords:
                    continue
                # Interpret sum of topicStrengths as term frequency
                tf[term] += topicStrength
                # Only consider first term in description if brandOnly=True
                if brandOnly:
                    break
        topicTFs.append(tf)
    return topicTFs

def combineTFandIDF(topicTFs, termIDFs):
    """
    Get sparse TF-IDF vector for each topic by combining TFs with externally
    supplied IDFs.
    """
    topicTFIDFs = []
    for tf in topicTFs:
        tfidf = []
        for term in tf:
            if term not in termIDFs:
                print >> sys.stderr, 'WARNING: No IDF for TF term: %s' % term
                continue
            tfidf.append((term, tf[term] * termIDFs[term]))
        # Sort terms by tfidf
        tfidf.sort(key=lambda tup: tup[1], reverse=True)
        topicTFIDFs.append(tfidf)
    return topicTFIDFs

def getTermDFs(topicTFs):
    """Get term "document" frequencies, where document are topics"""
    df = defaultdict(int)
    for tf in topicTFs:
        for term in tf:
            df[term] += 1
    return df

def getTopicTFIDFs(topicTFs):
    """Get sparse TF-IDF vector for each topic, where "documents" are topics"""
    topicTFIDFs = []
    df = getTermDFs(topicTFs)
    for tf in topicTFs:
        tfidf = [(term, tf[term] * math.log(len(topicTFs) / df[term]))\
                 for term, tf_val in tf.items()]
        # Sort terms by tfidf
        tfidf.sort(key=lambda tup: tup[1], reverse=True)
        topicTFIDFs.append(tfidf)
    return topicTFIDFs

def main():
    # Parse options
    usage = 'Usage: %prog [options] <database modelfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    dbFilename = getAndCheckFilename(args[0])
    modelFilename = getAndCheckFilename(args[1])

    # connect to db
    print 'Connecting to database %s. . .' % dbFilename
    db_conn = sqlite3.connect(dbFilename)

    if modelFilename.endswith('.pickle'):
        # load LDA model
        print 'Loading LDA model. . .'
        with open(modelFilename, 'r') as f:
            model = pickle.load(f)
        topicDists = [model.show_topic(topic, topn=options.topn)\
                      for topic in range(model.num_topics)]
    elif modelFilename.endswith('.npz'):
        # load LSI model
        print 'Loading LSI model. . .'
        npzfile = np.load(modelFilename)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        dictionary = npzfile['dictionary']
        topicDists_top = [
            showConcept(u, concept, topn=options.topn,
                            dictionary=dictionary)\
            for concept in range(len(s))
        ]
        topicDists_bot = [
            showConcept(u, concept, topn=options.topn,
                            dictionary=dictionary, reverse=False)\
            for concept in range(len(s))
        ]
        topicDists = []
        for i in range(len(s)):
            topicDists.append(topicDists_top[i] + topicDists_bot[i])
    else:
        print >> sys.stderr,\
            'error: Input must be either a .pickle or .npz file.'
        sys.exit(-1)

    # get stop words
    print 'Loading stopwords form %s. . .' % options.stopwords
    stopwords = getStopwords(options.stopwords)

    # get TFs
    topicTFs = getTopicTFs(db_conn, topicDists, stopwords=stopwords,
                           brandOnly=options.brandOnly)

    # get TF-IDFs
    if options.idfname is not None:
        print 'Loadng IDFs from %s. . .' % options.idfname
        termIDFs = loadPickle(options.idfname)
        topicTFIDFs = combineTFandIDF(topicTFs, termIDFs)
    else:
        print 'Computing IDFs with topics as documents. . .'
        topicTFIDFs = getTopicTFIDFs(topicTFs)

    # dump TF-IDFS
    pickle.dump(topicTFIDFs, open(options.savefile, 'w'))

    # Print the `topnPrint` terms for each topic
    if options.verbose:
        for topic in range(len(topicDists)):
            print ''
            print 'Top words for topic %d' % topic
            print '======================='
            for i in range(options.topnPrint):
                print '%s : %.3f' % (
                    topicTFIDFs[topic][i][0],
                    topicTFIDFs[topic][i][1]
                )

if __name__ == '__main__':
    main()
