#!/usr/bin/env python

"""
Compute a sparse TF-IDF vectors for each topic of an LDA model.
"""

from stemming.porter2 import stem
from optparse import OptionParser
from collections import defaultdict
import pickle
import os
import sys
import sqlite3

# db params
selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-i', '--idfname', dest='idfname',
        help='Name of pickle with saved idfs')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=100,
        help='Number of items per topic to print.', metavar='NUM')
    parser.add_option('-k', '--topnWords', type='int', dest='topnWords',
        default=10, help='Number of words per topic to print.', metavar='NUM')
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/tfidfs.pickle',
        help='Name of pickle to save tfidfs per topic.')
    return parser

def getTopWordsByTopic(db_conn, model, idf, topn):
    db_curs = db_conn.cursor()
    tfidfPerTopic = []
    for topic in range(model.num_topics):
        item_dist = model.show_topic(topic, topn=topn)
        tf = defaultdict(float)
        # Count terms over descriptions of all topn products to determine tf
        for i in range(topn):
            topicStrength = item_dist[i][0]
            item = item_dist[i][1]
            db_curs.execute(selectDescriptionStmt, (item,))
            description = db_curs.fetchone()[0]
            words = [stem(word.lower()) for word in description.split()]
            for word in words:
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
    usage = 'Usage: %prog [options] <lda.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return

    # connect to db
    db_conn = sqlite3.connect(options.dbname)

    # load lda model
    print 'Load LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get IDFs
    print 'Load IDFs. . .'
    idfpickle = options.idfname
    with open(idfpickle, 'r') as f:
        idf = pickle.load(f)

    # get top words for each topic 
    print 'Get top words. . .'
    tfidfs = getTopWordsByTopic(db_conn, model, idf, options.topn)

    # dump tf-idfs
    pickle.dump(tfidfs, open(options.outputpickle, 'w'))

    # Print the topnWords
    for topic in range(model.num_topics):
        print ''
        print 'Top words for topic %d' % topic
        print '======================='
        for i in range(options.topnWords):
            print '%s : %.3f' % (tfidfs[topic][i][0], tfidfs[topic][i][1])

if __name__ == '__main__':
    main()
