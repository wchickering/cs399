#!/usr/bin/env python

"""
Computes IDFs for terms in product descriptions, treating each product as a
"document".
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
selectShortDescriptionStmt =\
   ('SELECT Id, ShortDescription '
    'FROM Products '
    'WHERE Id in '
    '(SELECT Id FROM Categories '
     'WHERE parentCategory = :parentCategory '
     'AND category = :category)')
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
    parser.add_option('--savefile', dest='savefile', default='data/idf.pickle',
        help='Name of pickle to save idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords', default=None,
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--short-only', action='store_true', dest='shortOnly',
        default=False, help='Limit text to that in short descriptions.')
    parser.add_option('--bigrams', action='store_true', dest='bigrams',
        default=False, help='Include bigrams as well as unigrams.')
    parser.add_option('--include-categories', action='store_true',
        dest='includeCategories', default=False, help='Include categories.')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def calculateIDFs(db_conn, parentCategory, category, stopwords=None,
                  shortOnly=False, bigrams=False, includeCategories=False,
                  brandOnly=False):
    db_curs = db_conn.cursor()
    db_curs2 = db_conn.cursor()
    print 'Reading category products. . .'
    if shortOnly:
        db_curs.execute(selectShortDescriptionStmt, (parentCategory, category))
    else:
        db_curs.execute(selectDescriptionStmt, (parentCategory, category))
    numProducts = 0
    wordDocCounts = defaultdict(int)
    for row in db_curs:
        numProducts += 1
        item = row[0]
        description = row[1]
        if includeCategories:
            db_curs2.execute(selectCategoriesStmt, {'Id': item})
            description += ' ' + ' '.join(r[0] for r in db_curs2.fetchall())
        # strip out punctuation
        description = ''.join(ch for ch in description\
                              if ch not in string.punctuation)
        # stem words
        terms = [stem(w.lower()) for w in description.split()]
        seen = set()
        lastTerm = None
        for term in terms:
            # skip stop words
            if stopwords is not None and term in stopwords:
                continue
            # ignore duplicate terms
            if term not in seen:
                seen.add(term)
                wordDocCounts[term] += 1
            if bigrams and lastTerm is not None:
                bg = ' '.join([lastTerm, term])
                if bg not in seen:
                    seen.add(bg)
                    wordDocCounts[bg] += 1
            lastTerm = term
            # only consider first term in description if brandOnly=True
            if brandOnly:
                break
    print 'Calculating IDFs for %d items. . .' % numProducts
    idf = {}
    for term in wordDocCounts:
        idf[term] = math.log(float(numProducts) / wordDocCounts[term])
    return idf

def main():
    # Parse options
    usage = 'Usage: %prog [options] database parent category'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    dbname = getAndCheckFilename(args[0])
    parent = args[1]
    category = args[2]

    # Connect to db
    print 'Connecting to database %s. . .' % dbname
    db_conn = sqlite3.connect(dbname)

    # get stop words
    if options.stopwords is not None:
        print 'Loading stopwords from %s. . .' % options.stopwords
        stopwords = getStopwords(options.stopwords)
    else:
        stopwords = None

    # Calculate idfs over all products
    idf = calculateIDFs(db_conn, parent, category, stopwords=stopwords,
                        shortOnly=options.shortOnly, bigrams=options.bigrams,
                        includeCategories=options.includeCategories,
                        brandOnly=options.brandOnly)
    print 'Computed IDFs for %d terms.' % len(idf)

    # Dump results
    pickle.dump(idf, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
