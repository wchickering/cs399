#!/usr/bin/env python

"""
Compute sparse TF-IDF vectors for all products in a particular category,
treating each product as a "document".
"""

from optparse import OptionParser
from collections import defaultdict
from stemming.porter2 import stem
import pickle
import os
import sys
import math
import sqlite3
import string

# local modules
from Util import getAndCheckFilename, getStopwords

# db_params
selectDescriptionStmt =\
   ('SELECT Id, Description '
    'FROM Products '
    'WHERE Id in '
    '(SELECT Id FROM Categories '
     'WHERE parentCategory = :parentCategory '
     'AND category = :category)')
selectDescriptionStmt2 =\
   ('SELECT Id, Description, ShortDescription '
    'FROM Products '
    'WHERE Id in '
    '(SELECT Id FROM Categories '
     'WHERE parentCategory = :parentCategory '
     'AND category = :category)')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile', default='tfidfs.pickle',
        help='Name of pickle to save idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords', default=None,
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--short', action='store_true', dest='short',
        default=False, help='Include TF-IDF vectors from short descriptions.')
    parser.add_option('--bigrams', action='store_true', dest='bigrams',
        default=False, help='Include TF-IDF vectors for bigrams.')
    return parser

def getTerms(text, stopwords=None):
    # strip out punctuation
    text = ''.join(ch for ch in text if ch not in string.punctuation)
    # stem words
    terms = [stem(term.lower()) for term in text.split()]
    # remove stop words
    if stopwords is not None:
        terms = [term for term in terms if term not in stopwords]
    return terms

def getBigrams(terms):
    """Returns a list of bigrams for a list of TERMS."""
    bigrams = []
    lastTerm = None
    for term in terms:
        if lastTerm is not None:
            bigrams.append(' '.join([lastTerm, term]))
        lastTerm = term
    return bigrams

def computeTFs(terms, termDocCounts):
    """
    Compute term frequencies and update term document counts, TERMDOCCOUNTS,
    given a document consisting of TERMS.
    """
    tfs = defaultdict(int)
    seen = set()
    for term in terms:
        tfs[term] += 1
        if term not in seen:
            seen.add(term)
            termDocCounts[term] += 1
    return tfs

def computeTFIDFs(tfs, termDocCounts, numDocs):
    """
    Returns a sparse TF-IDF vector given a sparse vector of term frequencies,
    TFS, given the term document counts, TERMDOCCOUNTS, and number of documents,
    NUMDOCS.
    """
    tfidfs = {}
    for item in tfs:
        tfidfs[item] = defaultdict(float)
        for term, tf in tfs[item].items():
            tfidfs[item][term] = tf*math.log(float(numDocs)/termDocCounts[term])
    return tfidfs

def getTFIDFs(db_conn, parentCategory, category, stopwords,
              includeShort=False, includeBigrams=False):
    # compute TF vectors and term document counts
    tfs = {}
    tfs['terms'] = {}
    termDocCounts = defaultdict(int)
    if includeShort:
        tfs['short'] = {}
        shortDescTermDocCounts = defaultdict(int)
    if includeBigrams:
        tfs['bigrams'] = {}
        bigramDocCounts = defaultdict(int)
    db_curs = db_conn.cursor()
    if includeShort:
        db_curs.execute(selectDescriptionStmt2, (parentCategory, category))
    else:
        db_curs.execute(selectDescriptionStmt, (parentCategory, category))
    numDocs = 0
    for row in db_curs:
        numDocs += 1
        item = row[0]
        terms = getTerms(row[1], stopwords=stopwords)
        tfs['terms'][item] = computeTFs(terms, termDocCounts)
        if includeShort:
            tfs['short'][item] = computeTFs(
                getTerms(row[2], stopwords=stopwords), shortDescTermDocCounts
            )
        if includeBigrams:
            tfs['bigrams'][item] = computeTFs(
                getBigrams(terms), bigramDocCounts
            )
    # use TF vectors and term document counts to compute TF-IDF vectors
    tfidfs = {}
    tfidfs['terms'] = computeTFIDFs(tfs['terms'], termDocCounts, numDocs)
    if includeShort:
        tfidfs['short'] = computeTFIDFs(
            tfs['short'], shortDescTermDocCounts, numDocs
        )
    if includeBigrams:
        tfidfs['bigrams'] = computeTFIDFs(
            tfs['bigrams'], bigramDocCounts, numDocs
        )
    return tfidfs

def main():
    # Parse options
    usage = 'Usage: %prog [options] database parentCategory category'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    dbname = getAndCheckFilename(args[0])
    parentCategory = args[1]
    category = args[2]

    # Connect to db
    db_conn = sqlite3.connect(dbname)

    # get stop words
    if options.stopwords is not None:
        print 'Loading stopwords from %s. . .' % options.stopwords
        stopwords = getStopwords(options.stopwords)
    else:
        stopwords = None

    # get TF-IDF vectors
    tfidfs = getTFIDFs(db_conn, parentCategory, category, stopwords=stopwords,
                       includeShort=options.short,
                       includeBigrams=options.bigrams)

    # save results to disk
    pickle.dump(tfidfs, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
