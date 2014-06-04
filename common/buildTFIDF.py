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
selectDescriptionStmt =\
    ('SELECT Description '
     'FROM Products '
     'WHERE Id = :Id')
selectShortDescriptionStmt =\
    ('SELECT ShortDescription '
     'FROM Products '
     'WHERE Id = :Id')
selectCategoriesStmt =\
    ('SELECT DISTINCT ParentCategory '
     'FROM Categories '
     'WHERE Id = :Id '
     'UNION '
     'SELECT DISTINCT Category '
     'FROM Categories '
     'WHERE Id = :Id')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-i', '--idfname', dest='idfname', default=None,
        help='Name of pickle with saved idfs', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=None,
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
    parser.add_option('--short-only', action='store_true', dest='shortOnly',
        default=False, help='Limit text to that in short descriptions.')
    parser.add_option('--bigrams', action='store_true', dest='bigrams',
        default=False, help='Include bigrams as well as unigrams.')
    parser.add_option('--no-idf', action='store_true', dest='noIDF',
        default=False, help='Set IDF=1 for all terms.')
    parser.add_option('--include-categories', action='store_true',
        dest='includeCategories', default=False, help='Include categories.')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def getTopicDists(filenames, topn=None):
    topicDists = []
    for filename in filenames:
        if filename.endswith('.pickle'):
            # load LDA model
            print 'Loading LDA model from %s. . .' % filename
            with open(filename, 'r') as f:
                model = pickle.load(f)
            topicDists += [model.show_topic(
                    topic,
                    topn=(topn if topn is not None else len(model.id2word))
                ) for topic in range(model.num_topics)]
        elif filename.endswith('.npz'):
            # load LSI model
            print 'Loading LSI model from %s. . .' % filename
            npzfile = np.load(filename)
            u = npzfile['u']
            s = npzfile['s']
            v = npzfile['v']
            dictionary = npzfile['dictionary']
            if topn is not None and topn < u.shape[0]/2:
                topicDists_top = [showConcept(
                        u,
                        concept,
                        topn=topn,
                        dictionary=dictionary
                    ) for concept in range(len(s))]
                topicDists_bot = [showConcept(
                        u,
                        concept,
                        topn=topn,
                        dictionary=dictionary,
                        reverse=False
                    ) for concept in range(len(s))]
                for i in range(len(s)):
                    topicDists.append(topicDists_top[i] + topicDists_bot[i])
            else:
                topicDists += [showConcept(
                        u,
                        concept,
                        topn=u.shape[0],
                        dictionary=dictionary
                    ) for concept in range(len(s))]
        else:
            print >> sys.stderr,\
                'error: Input must be either a .pickle or .npz file.'
            sys.exit(-1)
    return topicDists

def getTopicTFs(db_conn, topicDists, stopwords=None, shortOnly=False,
                bigrams=False, includeCategories=False, brandOnly=False):
    db_curs = db_conn.cursor()
    db_curs2 = db_conn.cursor()
    topicTFs = []
    for topic in range(len(topicDists)):
        tf = defaultdict(float)
        for i in range(len(topicDists[topic])):
            topicStrength = topicDists[topic][i][0]
            item = topicDists[topic][i][1]
            if shortOnly:
                db_curs.execute(selectShortDescriptionStmt, (item,))
            else:
                db_curs.execute(selectDescriptionStmt, (item,))
            row = db_curs.fetchone()
            description = row[0]
            if includeCategories:
                db_curs2.execute(selectCategoriesStmt, {'Id': item})
                description += ' ' + ' '.join(r[0] for r in db_curs2.fetchall())
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
                # interpret sum of topicStrengths as term frequency
                tf[term] += topicStrength
                if bigrams and lastTerm is not None:
                    bg = ' '.join([lastTerm, term])
                    tf[bg] += topicStrength
                lastTerm = term
                # only consider first term in description if brandOnly=True
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

def getTopicTFIDFs(topicTFs, allTopicTFs):
    """Get sparse TF-IDF vector for each topic, where "documents" are topics"""
    df = getTermDFs(allTopicTFs)
    topicTFIDFs = []
    for tf in topicTFs:
        tfidf = [(term, tf[term] * math.log(len(allTopicTFs) / df[term]))\
                 for term, tf_val in tf.items()]
        # Sort terms by tfidf
        tfidf.sort(key=lambda tup: tup[1], reverse=True)
        topicTFIDFs.append(tfidf)
    return topicTFIDFs

def getTFIDFsansIDF(topicTFs):
    """Get sparse TF-IDF vectors in which IDF=1 for all terms"""
    topicTFIDFs = []
    for tf in topicTFs:
        tfidf = [(term, tf[term]) for term, tf_val in tf.items()]
        # Sort terms by tfidf
        tfidf.sort(key=lambda tup: tup[1], reverse=True)
        topicTFIDFs.append(tfidf)
    return topicTFIDFs

def main():
    # Parse options
    usage = 'Usage: %prog [options] database modelfile1 [modelfile2] [...]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('Wrong number of arguments')
    dbFilename = getAndCheckFilename(args[0])
    modelFilenames = args[1:]

    # connect to db
    print 'Connecting to database %s. . .' % dbFilename
    db_conn = sqlite3.connect(dbFilename)

    # get topic distributions
    # Multiple (e.g. 2) models can be given such that IDF may be
    # computed considering ALL topics as the documents in a corpus.
    topicDists = getTopicDists([modelFilenames[0]], topn=options.topn)
    if len(modelFilenames) > 1:
        allTopicDists = getTopicDists(modelFilenames, options.topn)
    else:
        allTopicDists = None

    # get stop words
    print 'Loading stopwords form %s. . .' % options.stopwords
    stopwords = getStopwords(options.stopwords)

    # get TFs
    print 'Computing term frequencies. . .'
    topicTFs = getTopicTFs(db_conn, topicDists, stopwords=stopwords,
                           shortOnly=options.shortOnly, bigrams=options.bigrams,
                           includeCategories=options.includeCategories,
                           brandOnly=options.brandOnly)
    if allTopicDists is not None:
        allTopicTFs = getTopicTFs(db_conn, allTopicDists, stopwords=stopwords,
                                  shortOnly=options.shortOnly,
                                  bigrams=options.bigrams,
                                  includeCategories=options.includeCategories,
                                  brandOnly=options.brandOnly)
    else:
        alltopicTFs = None

    # get TF-IDFs
    if options.noIDF:
        topicTFIDFs = getTFIDFsansIDF(topicTFs)
    else:
        if options.idfname is not None:
            print 'Loadng IDFs from %s. . .' % options.idfname
            termIDFs = loadPickle(options.idfname)
            topicTFIDFs = combineTFandIDF(topicTFs, termIDFs)
        else:
            print 'Computing IDFs with topics as documents. . .'
            if allTopicTFs is not None:
                topicTFIDFs = getTopicTFIDFs(topicTFs, allTopicTFs)
            else:
                topicTFIDFs = getTopicTFIDFs(topicTFs, topicTFs)

    # dump TF-IDFS
    print 'Saving TF-IDFs to %s. . .' % options.savefile
    pickle.dump(topicTFIDFs, open(options.savefile, 'w'))

    # Print the `topnPrint` terms for each topic
    if options.verbose:
        for topic in range(len(topicDists)):
            tfidfs = [tup[1] for tup in topicTFIDFs[topic]]
            print ''
            print 'Top words for topic %d (num terms = %d, l2 norm = %0.3f)' % (
                topic,
                len(tfidfs),
                np.linalg.norm(tfidfs)
            )
            print '======================='
            for i in range(options.topnPrint):
                print '%s : %.3f' % (
                    topicTFIDFs[topic][i][0],
                    topicTFIDFs[topic][i][1]
                )

if __name__ == '__main__':
    main()
