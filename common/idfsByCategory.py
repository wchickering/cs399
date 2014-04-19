#!/usr/bin/env python

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import pickle
import os
import sys
import math
import sqlite3

from SessionTranslator import SessionTranslator

# db_params
selectProducts =\
   ('SELECT Id, Description '
    'FROM Products '
    'WHERE Id in '
    '(SELECT Id FROM Categories '
    'WHERE Category = :Category)')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        help='Name of pickle to save idfs')
    return parser

def calculateIDFs(dbname, category):
    numProducts = 0.0 
    wordDocCounts = {}
    idf = {}
    db_conn = sqlite3.connect(dbname)
    db_curs = db_conn.cursor()
    print 'executing database query...'
    db_curs.execute(selectProducts, (category,))
    print 'reading rows..'
    for row in db_curs:
        numProducts += 1
        if numProducts % 100000 == 0:
            print 'reading row ' + str(numProducts)
        productId = row[0]   
        description = row[1]
        words = description.split()
        uniqueWords = set(words)
        for word in uniqueWords:
            word = word.lower()
            if word in wordDocCounts: 
                wordDocCounts[word] += 1
            else:
                wordDocCounts[word] = 1
    print 'calculating idfs...'
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

    # calculate idfs over all products
    print 'calculating idfs...'
    idf = calculateIDFs(options.dbname, category)
    pickle.dump(idf, open(options.outputpickle, 'w'))

if __name__ == '__main__':
    main()
