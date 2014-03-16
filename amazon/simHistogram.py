#!/usr/local/bin/python

"""
Generate histogram data for similarity scores from a set of item pairs.
"""

from optparse import OptionParser
import sqlite3
import numpy
import csv
import os
import sys

import similarity

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
    parser.add_option('-b', '--bins', type='int', dest='numBins', default=20,
        help='Number of bins.', metavar='NUM')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1".'),
        metavar='FUNCNAME')
    return parser

def incrementBin(bins, cosineSim):
    bins[int(round((1.0 + cosineSim)*(len(bins) - 1)/2.0))] += 1

def makeHistogram(db_conn, inputfile, cosineFunc, bins):
    db_curs = db_conn.cursor()
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
        # compute biases
        bias1 = numpy.mean([review[2] for review in reviews1])
        bias2 = numpy.mean([review[2] for review in reviews2])
        cosineSim, numUserCommon =\
            cosineFunc(reviews1, reviews2, bias1, bias2)
        incrementBin(bins, cosineSim)
    return bins

def printHistogram(writer, bins):
    for i in range(len(bins)):
        writer.writerow([round((i + 0.5)*2.0/len(bins) - 1.0, 3), bins[i]])

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

    # Connect to db
    print >> sys.stderr, 'Connect to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Open input file
    print >> sys.stderr, 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # Generate histogram data
    bins = [0]*options.numBins
    bins = makeHistogram(db_conn, inputfile, cosineFunc, bins)

    # Print histogram data
    writer = csv.writer(sys.stdout)
    printHistogram(writer, bins)

if __name__ == '__main__':
    main()
