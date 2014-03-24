#!/usr/local/bin/python

"""
Returns average and variance of ratings associated with a list of product pairs.
"""

from optparse import OptionParser
import sqlite3
import numpy as np
import csv
import os
import sys

#db params
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
        help='Similarity function to use: "randSim" (default) or "prefSim"',
        metavar='FUNCNAME')
    return parser

def getRatings(db_conn, cosineFunc, inputfile):
    ratings = []
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        db_curs = db_conn.cursor()
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        # compute product biases
        bias1 = np.mean([review[2] for review in reviews1])
        bias2 = np.mean([review[2] for review in reviews2])
        if cosineFunc == 'prefSim':
            ratings += [review[2] - bias1 for review in reviews1]
            ratings += [review[2] - bias2 for review in reviews2]
        else: # randSim
            i = 0
            j = 0
            while i < len(reviews1) and j < len(reviews2):
                userId1 = reviews1[i][1]
                userId2= reviews2[j][1]
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
                    ratings.append(rating1)
                    ratings.append(rating2)
                    i += 1
                    j += 1
    return ratings

def aggregateRatings(db_conn, cosineFunc, inputfile):
    ratings = getRatings(db_conn, cosineFunc, inputfile)
    average = np.mean(ratings)
    if len(ratings) <= 1:
        variance = float('inf')
    else:
        variance = sum([(r - average)**2 for r in ratings])/(len(ratings) - 1)
    return average, variance

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
    if options.cosineFunc != 'randSim' and options.cosineFunc != 'prefSim':
        print >> sys.stderr, 'cosineFunc must be either randSim or prefSim'
        return

    # connect to db
    print >> sys.stderr, 'Connecting to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # open input file
    print >> sys.stderr, 'Reading from %s. . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # aggregate ratings
    average, variance = aggregateRatings(db_conn, options.cosineFunc, inputfile)

    # print output
    print 'Average = %0.5f, Variance = %0.05f' % (average, variance)

if __name__ == '__main__':
    main()
