#!/usr/local/bin/python

"""
Generates several histograms, one for each unique combination of rating values
assigned to a pair of products by a common reviewer. The histograms are binned
by the ultimate similarity score for the pair of products.
"""

from optparse import OptionParser
import sqlite3
import csv
import os
import sys

import similarity

# params
minRating = 1
maxRating = 5
outputFileTemplate = '%s_%d_%d.csv'
displayInterval = 10000

# db params
dbTimeout = 5
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore, Score '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir',
        default='ratingsVsSim', help='Output directory.', metavar='DIR')
    parser.add_option('-b', '--bins', type='int', dest='numBins', default=20,
        help='Number of bins.', metavar='NUM')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1".'),
        metavar='FUNCNAME')
    return parser

def initHistograms(minRating, maxRating, numBins):
    histograms = {}
    for rating1 in range(minRating, maxRating + 1):
        for rating2 in range(rating1, maxRating + 1):
            histograms[(rating1, rating2)] = [0]*numBins
    return histograms

def incrementBin(bins, cosineSim):
    bins[int(round((1.0 + cosineSim)*(len(bins) - 1)/2.0))] += 1

def makeHistograms(db_conn, inputfile, cosineFunc, histograms):
    db_curs = db_conn.cursor()
    count = 0
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [row for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [row for row in db_curs.fetchall()]
        # compute cosine similarity using the provided function.
        cosineSim, numUserCommon = cosineFunc(reviews1, reviews2)
        # update histograms
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
                count += 1
                rating1 = reviews1[i][3]
                rating2 = reviews2[j][3]
                minRating = min(rating1, rating2)
                maxRating = max(rating1, rating2)
                histogram = histograms[(minRating, maxRating)]
                incrementBin(histogram, cosineSim)
                i += 1
                j += 1
                if count % displayInterval == 0:
                    print '%d rating pairs processed' % count
    return histograms

def printHistograms(outputDir, simType, histograms):
    for rating1 in range(minRating, maxRating + 1):
        for rating2 in range(rating1, maxRating + 1):
            outputFileName = os.path.join(outputDir,
                outputFileTemplate % (simType, rating1, rating2))
            with open(outputFileName, 'wb') as csvfile:
                writer = csv.writer(csvfile)
                histogram = histograms[(rating1, rating2)]
                for i in range(len(histogram)):
                    writer.writerow([
                        round((i + 0.5)*2.0/len(histogram) - 1.0, 3),
                        histogram[i]])

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
    if not os.path.isdir(options.outputDir):
       print >> sys.stderr, 'Cannot find output dir: %s' % options.outputDir
       return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return

    # Connect to db
    print 'Connect to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Open input file
    print 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # Initialize histograms
    histograms = initHistograms(minRating, maxRating, options.numBins)

    # Generate histogram data
    histograms = makeHistograms(db_conn, inputfile, cosineFunc, histograms)

    # Output histograms
    printHistograms(options.outputDir, options.cosineFunc, histograms)

if __name__ == '__main__':
    main()

