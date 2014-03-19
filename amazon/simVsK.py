#!/usr/local/bin/python

"""
Computes the similarity between products as a function of the number of common
reviewers, K.
"""

from optparse import OptionParser
import sqlite3
import math
import os
import csv

import similarity

# params
outputFileTemplate = '%s_%s_%s.csv'

# db params
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId') 

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default='simVsK',
        help='Output directory.', metavar='DIR')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1"'), metavar='FUNCNAME')
    parser.add_option('-s', '--step', dest='step', type='int', default=1,
        help='Step size for K.', metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <csvfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return
    # Set the similarity step value
    similarity.step = options.step

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        with open(inputfilename, 'r') as inputfile:
            for line in inputfile:
                tokens = line.split(',')
                productId1 = tokens[0].strip()
                productId2 = tokens[1].strip()
                outputFileName =\
                    os.path.join(options.outputDir, outputFileTemplate %\
                    (options.cosineFunc, productId1, productId2))
                print 'Writing %s . . .' % outputFileName
                with open(outputFileName, 'wb') as csvfile:
                    similarity.writer = csv.writer(csvfile)
                    db_curs.execute(selectReviewsStmt, (productId1,))
                    reviews1 = [(row[0], row[1], row[2])\
                                for row in db_curs.fetchall()]
                    db_curs.execute(selectReviewsStmt, (productId2,))
                    reviews2 = [(row[0], row[1], row[2])\
                                for row in db_curs.fetchall()]
                    cosineFunc(reviews1, reviews2)

if __name__ == '__main__':
    main()
