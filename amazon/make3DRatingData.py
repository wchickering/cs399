#!/usr/local/bin/python

"""
Generate 3D histogram of rating pair data.
"""

from optparse import OptionParser
import sqlite3
import csv
import os
import sys
import numpy as np

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
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-1.5, help='Minimum rating.', metavar='NUM')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.075, help='Step rating.', metavar='NUM')
    parser.add_option('--numBins', type='int', dest='numBins',
        default=40, help='Number of bins on a side.', metavar='NUM')
    return parser

def incrementHistogram(histogram, minRating, stepRating, numBins,
                       rating1, rating2):
    if rating1 >= minRating and rating1 < minRating + numBins*stepRating and\
       rating2 >= minRating and rating2 < minRating + numBins*stepRating:
        idx1 = int(round((rating1 - minRating)/stepRating))
        idx2 = int(round((rating2 - minRating)/stepRating))
        if idx1 >= numBins:
            idx1 = numBins - 1
        if idx2 >= numBins:
            idx2 = numBins - 1
        histogram[idx1][idx2] += 1

def fillHistogram(db_conn, inputfile, histogram,
                  minRating, stepRating, numBins):
    db_curs = db_conn.cursor()
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        print >> sys.stderr, 'Processing %s, %s . . .' %\
                             (productId1, productId2)
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        # compute product biases:
        bias1 = np.mean([review[2] for review in reviews1])
        bias2 = np.mean([review[2] for review in reviews2])
        numUsersCommon = 0
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
                numUsersCommon += 1
                rating1 = reviews1[i][2] - bias1
                rating2 = reviews2[j][2] - bias2
                incrementHistogram(histogram, minRating, stepRating, numBins,
                                   rating1, rating2)
                i += 1
                j += 1

def printHistogram(writer, histogram, minRating, stepRating, numBins):
    for i in range(numBins):
        rating1 = minRating + i*stepRating
        for j in range(numBins):
            rating2 = minRating + j*stepRating
            writer.writerow([round(rating1, 3), round(rating2, 3),
                             histogram[i][j]])

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

    # Connect to db
    print >> sys.stderr, 'Connect to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Open input file
    print >> sys.stderr, 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # Initialize histogram
    histogram = [[0 for x in xrange(options.numBins)]\
                    for x in xrange(options.numBins)]

    # Fill histogram
    fillHistogram(db_conn, inputfile, histogram,
                  options.minRating, options.stepRating, options.numBins)

    # Print histogram
    writer = csv.writer(sys.stdout)
    printHistogram(writer, histogram,
                   options.minRating, options.stepRating, options.numBins)

if __name__ == '__main__':
    main()
