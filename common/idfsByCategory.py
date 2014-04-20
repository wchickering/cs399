#!/usr/bin/env python

from optparse import OptionParser
import pickle
import os
import sys
import math
import sqlite3
from collections import defaultdict
from stemming.porter2 import stem

# params
displayInterval = 10000

# db_params
selectCategoryProductsStmt =\
   ('SELECT Description '
    'FROM Products '
    'WHERE Id in '
    '(SELECT Id FROM Categories '
    'WHERE Category = :Category)')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db', help='Name of Sqlite3 product database.',
        metavar='DBNAME')
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/idf.pickle', help='Name of pickle to save idfs')
    parser.add_option('--stopwords', dest='stopwords',
        default='data/stopwords.txt',
        help='File containing a comma separated list of stop words.')
    return parser

def calculateIDFs(db_conn, category, stopwords=None):
    db_curs = db_conn.cursor()
    print 'Reading category products. . .'
    db_curs.execute(selectCategoryProductsStmt, (category,))
    numProducts = 0
    wordDocCounts = defaultdict(int)
    for row in db_curs:
        numProducts += 1
        if numProducts % displayInterval == 0:
            print '%d Products' % numProducts
        description = row[0]
        words = set([stem(w.lower()) for w in description.split()])
        for word in words:
            if stopwords is not None and word in stopwords:
                continue
            wordDocCounts[word] += 1
    print 'Calculating IDFs. . .'
    idf = {}
    for word in wordDocCounts:
        idf[word] = math.log(numProducts / wordDocCounts[word])
    return idf

def main():
    # Parse options
    usage = 'Usage: %prog [options] category'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    category = args[0]

    # Connect to db
    db_conn = sqlite3.connect(options.dbname)

    # get stop words
    if os.path.isfile(options.stopwords):
        with open(options.stopwords, 'r') as f:
            try:
                stopwords = f.readline().split(',')
            except:
                print >> sys.stderr, 'Failed to parse stop words.'
                return
    else:
        print >> sys.stderr,\
            'WARNING: stop words file not found: %s' % options.stopwords
        stopwords = None

    # Calculate idfs over all products
    idf = calculateIDFs(db_conn, category, stopwords=stopwords)
    print 'Computed IDFs for %d terms.' % len(idf)

    # Dump results
    pickle.dump(idf, open(options.outputpickle, 'w'))

if __name__ == '__main__':
    main()
