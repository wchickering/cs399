#!/usr/local/bin/python

"""
Generates several histograms, each corresponding to a pair of rating ranges
assigned to a pair of products by a common reviewer. The histograms are binned
by the ultimate similarity score for the pair of products.
"""

from optparse import OptionParser
import sqlite3
import numpy
import collections
import csv
import os
import sys

import similarity

# params
outputFileTemplateTemplate = '%s_%s_%%0.3f_%%0.3f.csv'
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
              '"prefSimAlt1", or "randSimAlt1".'), metavar='FUNCNAME')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=0.5, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=5.5, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=1.0, help='Step rating.', metavar='FLOAT')
    parser.add_option('-t', '--ratingType', dest='ratingType', default='raw',
              help='Rating type to use: "raw" (default), or "adjusted"',
              metavar='FUNCNAME')
    return parser

class Histograms(collections.MutableMapping):
    """A dictionary of histograms indexed by rating pairs."""
    def __init__(self, minRating, maxRating, stepRating, numBins):
        self.minRating = minRating
        self.maxRating = maxRating
        self.stepRating = stepRating
        self.store = {}
        # initialize histograms
        for key in self:
            self[key] = [0]*numBins
        # include null histogram to return for bad keys
        self[(self.maxRating, self.maxRating)] = None

    def __keytransform__(self, key):
        rating1 = min(key[0], key[1])
        rating2 = max(key[0], key[1])
        if rating1 < self.minRating or rating2 >= self.maxRating:
            return -1
        idx = 0
        p = self.minRating
        while p < self.maxRating:
            q = p
            while q < self.maxRating:
                if rating1 >= p and rating1 < p + self.stepRating and\
                   rating2 >= q and rating2 < q + self.stepRating:
                    return idx
                idx += 1
                q += self.stepRating
            p += self.stepRating
        raise Exception("Unreachable code.")

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __len__(self):
        return len(self.store)

    def __iter__(self):
        self.current = [self.minRating, self.minRating]
        return self

    def next(self):
        if self.current[0] >= self.maxRating - self.stepRating and\
           self.current[1] >= self.maxRating:
            raise StopIteration
        elif self.current[1] >= self.maxRating:
           self.current[0] += self.stepRating
           self.current[1] = self.current[0] + self.stepRating
        else:
           self.current[1] += self.stepRating
        return (self.current[0], self.current[1] - self.stepRating)

def incrementBin(bins, cosineSim):
    bins[int(round((1.0 + cosineSim)*(len(bins) - 1)/2.0))] += 1

def fillHistograms(db_conn, inputfile, cosineFunc, ratingType, histograms):
    db_curs = db_conn.cursor()
    count = 0
    bad_keys = 0
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
        # compute product biases
        bias1 = numpy.mean([review[2] for review in reviews1])
        bias2 = numpy.mean([review[2] for review in reviews2])
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
                if ratingType == 'adjusted':
                    rating1 = reviews1[i][2] - bias1
                    rating2 = reviews2[j][2] - bias2
                else:
                    rating1 = reviews1[i][3]
                    rating2 = reviews2[j][3]
                histogram = histograms[(rating1, rating2)]
                if not histogram:
                    bad_keys += 1
                else:
                    count += 1
                    incrementBin(histogram, cosineSim)
                    if count % displayInterval == 0:
                        print '%d rating pairs processed' % count
                i += 1
                j += 1
    print '%d Bad Keys.' % bad_keys

def printHistograms(outputDir, outputFileTemplate, histograms):
    for key in histograms:
        rating1 = key[0]
        rating2 = key[1]
        histogram = histograms[(rating1, rating2)]
        outputFileName = os.path.join(outputDir,
            outputFileTemplate % (rating1, rating2))
        print 'Writing to %s . . .' % outputFileName
        with open(outputFileName, 'wb') as csvfile:
            writer = csv.writer(csvfile)
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
    histograms = Histograms(options.minRating, options.maxRating,
                            options.stepRating, options.numBins)

    # Generate histogram data
    fillHistograms(db_conn, inputfile, cosineFunc, options.ratingType,
                   histograms)

    # Output histograms
    outputFileTemplate = outputFileTemplateTemplate %\
                         (options.cosineFunc, options.ratingType)
    printHistograms(options.outputDir, outputFileTemplate, histograms)

if __name__ == '__main__':
    main()

