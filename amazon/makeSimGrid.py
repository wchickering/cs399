#!/usr/local/bin/python

"""
Compute the average similarity scores associated with rating pairs.
"""

from optparse import OptionParser
import sqlite3
import numpy
import csv
import os
import sys
import collections

import similarity
from SimilarityGrid import SimilarityGrid

# db params
dbTimeout = 5
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='randSim',
        help='Similarity function to use: "prefSim" or "randSim" (default)',
        metavar='FUNCNAME')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-2.0, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=2.0, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.1, help='Step rating.', metavar='FLOAT')
    return parser

def fillGrid(db_conn, inputfile, cosineFunc, simGrid):
    count = 0
    bad_keys = 0
    db_curs = db_conn.cursor()
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        print >> sys.stderr, '%s, %s' % (productId1, productId2)
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [row for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [row for row in db_curs.fetchall()]
        # compute cosine similarity using the provided function.
        cosineSim, numUserCommon = cosineFunc(reviews1, reviews2)
        # compute product biases
        bias1 = numpy.mean([review[2] for review in reviews1])
        bias2 = numpy.mean([review[2] for review in reviews2])
        # update grid
        i = 0
        j = 0
        while i < len(reviews1) and j < len(reviews2):
            userId1 = reviews1[i][1]
            userId2 = reviews2[j][1]
            if userId1 < userId2:
                i += 1
            elif userId1 > userId2:
                j += 1
            else:
                time1 = reviews1[i][0]
                time2 = reviews2[j][0]
                if time1 == time2:
                    i += 1
                    j += 1
                    continue # ignore duplicate reviews
                rating1 = reviews1[i][2] - bias1
                rating2 = reviews2[j][2] - bias2
                #print 'rating1 = %0.3f, rating2 = %0.3f' % (rating1, rating2)
                if simGrid[(rating1, rating2)]:
                    count += 1
                    simGrid[(rating1, rating2)][0] += cosineSim
                    simGrid[(rating1, rating2)][1] += 1
                else:
                    bad_keys += 1
                i += 1
                j += 1
    print >> sys.stderr, '%d Bad Keys.' % bad_keys

def main():
    # Parse options
    usage = 'Usage: %prog [options] <csvfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputFileName = args[0]
    if not os.path.isfile(inputFileName):
        print >> sys.stderr, 'Cannot find input file: %s' % inputFileName
        return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return

    # Initialize similarity grid
    simGrid = SimilarityGrid(options.minRating, options.maxRating,
                             options.stepRating)

    # Open input file
    print >> sys.stderr, 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # Connect to db
    print >> sys.stderr, 'Connect to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Fill similarity grid
    fillGrid(db_conn, inputfile, cosineFunc, simGrid)

    # Write similarity grid to stdout
    simGrid.writeToFile(sys.stdout)

if __name__ == '__main__':
    main()

