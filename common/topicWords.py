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

# local modules
import LSI_util as lsi

# db params
selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-i', '--idfname', dest='idfname',
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=100,
        help='Number of items per topic to print.', metavar='NUM')
    parser.add_option('-k', '--topnWords', type='int', dest='topnWords',
        default=10, help='Number of words per topic to print.', metavar='NUM')
    parser.add_option('-v', '--verbose', 
        action='store_true', dest='verbose', default=False,
        help='Print top words')
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/tfidf.pickle',
        help='Name of pickle to save tfidfs per topic.', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords',
        default='data/stopwords.txt',
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    return parser

def getTopWordsByTopic(db_conn, topicDists, idf, stopwords=None):
    db_curs = db_conn.cursor()
    tfidfPerTopic = []
    for topic in range(len(topicDists)):
        tf = defaultdict(float)
        # Count terms over descriptions of all topn products to determine tf
        for i in range(len(topicDists[topic])):
            topicStrength = topicDists[topic][i][0]
            item = topicDists[topic][i][1]
            db_curs.execute(selectDescriptionStmt, (item,))
            description = db_curs.fetchone()[0]
            # strip out punctuation
            description = ''.join(ch for ch in description\
                                  if ch not in string.punctuation)
            words = [stem(word.lower()) for word in description.split()]
            for word in words:
                if stopwords is not None and word in stopwords:
                    continue
                tf[word] += topicStrength
        # Sort words by tfidf
        tfidfs = []
        for word in tf: 
            if word not in idf:
                continue
            tfidfScore = tf[word] * idf[word]
            tfidf = (word, tfidfScore)
            tfidfs.append(tfidf)
        tfidfs.sort(key=lambda tup: tup[1], reverse=True)
        tfidfPerTopic.append(tfidfs)
    return tfidfPerTopic

def main():
    # Parse options
    usage = 'Usage: %prog [options] modelfile'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    filename = args[0]
    if not os.path.isfile(filename):
        print >> sys.stderr, 'error: Cannot find %s' % filename
        return

    if filename.endswith('.pickle'):
        # load LDA model
        print 'Loading LDA model. . .'
        with open(filename, 'r') as f:
            model = pickle.load(f)
        topicDists = [model.show_topic(topic, topn=options.topn)\
                      for topic in range(model.num_topics)]
    elif filename.endswith('.npz'):
        # load LSI model
        print 'Loading LSI model. . .'
        npzfile = np.load(filename)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        dictionary = npzfile['dictionary']
        topicDists = [lsi.showConcept(u, concept, topn=options.topn,
                                      dictionary=dictionary)\
                      for concept in range(len(s))]
    else:
        print >> sys.stderr,\
            'error: Input must be either a .pickle or .npz file.'
        return

    # connect to db
    db_conn = sqlite3.connect(options.dbname)

    # get stop words
    if os.path.isfile(options.stopwords):
        with open(options.stopwords, 'r') as f:
            try:
                stopwords = f.readline().split(',')
            except:
                print >> sys.stderr, 'error: Failed to parse stop words.'
                return
    else:
        print >> sys.stderr,\
            'warning: stop words file not found: %s' % options.stopwords
        stopwords = None

    # get IDFs
    print 'Load IDFs. . .'
    with open(options.idfname, 'r') as f:
        idf = pickle.load(f)

    # get top words for each topic 
    print 'Get top words. . .'
    tfidf = getTopWordsByTopic(db_conn, topicDists, idf, stopwords=stopwords)

    # dump tf-idfs
    pickle.dump(tfidf, open(options.outputpickle, 'w'))

    # Print the topnWords
    if options.verbose:
        for topic in range(len(topicDists)):
            print ''
            print 'Top words for topic %d' % topic
            print '======================='
            for i in range(options.topnWords):
                print '%s : %.3f' % (tfidf[topic][i][0], tfidf[topic][i][1])

if __name__ == '__main__':
    main()
