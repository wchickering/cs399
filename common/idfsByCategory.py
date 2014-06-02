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
from Util import getStopwords

# db_params
selectCategoryProductsStmt =\
   ('SELECT Id, Description '
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
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Name of Sqlite3 product database.',
        metavar='DBNAME')
    parser.add_option('--savefile', dest='savefile', default='data/idf.pickle',
        help='Name of pickle to save idfs', metavar='FILE')
    parser.add_option('--stopwords', dest='stopwords',
        default='data/stopwords.txt',
        help='File containing a comma separated list of stop words.',
        metavar='FILE')
    parser.add_option('--include-categories', action='store_true',
        dest='includeCategories', default=False, help='Include categories.')
    parser.add_option('--brand-only', action='store_true', dest='brandOnly',
        default=False,
        help='Only consider brand (i.e. first term in description).')
    return parser

def calculateIDFs(db_conn, parentCategory, category, stopwords=None,
                  includeCategories=False, brandOnly=False):
    db_curs = db_conn.cursor()
    db_curs2 = db_conn.cursor()
    print 'Reading category products. . .'
    db_curs.execute(selectCategoryProductsStmt, (parentCategory, category))
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
        if brandOnly:
            # Only consider first word of description if brandOnly=True
            # must use a list to preserve word order
            words = [stem(w.lower()) for w in description.split()]
        else:
            words = set([stem(w.lower()) for w in description.split()])
        for word in words:
            if stopwords is not None and word in stopwords:
                continue
            wordDocCounts[word] += 1
            if brandOnly:
                break
    print 'Calculating IDFs for %d items. . .' % numProducts
    idf = {}
    for word in wordDocCounts:
        idf[word] = math.log(numProducts / wordDocCounts[word])
    return idf

def main():
    # Parse options
    usage = 'Usage: %prog [options] parent category'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    parent = args[0]
    category = args[1]

    # Connect to db
    db_conn = sqlite3.connect(options.dbname)

    # get stop words
    stopwords = getStopwords(options.stopwords)

    # Calculate idfs over all products
    idf = calculateIDFs(db_conn, parent, category, stopwords=stopwords,
                        includeCategories=options.includeCategories,
                        brandOnly=options.brandOnly)
    print 'Computed IDFs for %d terms.' % len(idf)

    # Dump results
    pickle.dump(idf, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
