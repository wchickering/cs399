#!/usr/local/bin/python

from optparse import OptionParser
import sqlite3
import csv
import os
import sys
import random
import numpy

import similarity
from cosineSimSim import cosineSimSim

# params
outputTemplateTemplate = '%s_%%s_%%s.csv'

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
    parser.add_option('-o', '--output-dir', dest='outputDir',
        default='predictions', help='Output directory.', metavar='DIR')
    parser.add_option('--randomSeed', type='int', dest='randomSeed',
        default=0, help='Seed for random module.', metavar='NUM')
    parser.add_option('--dimensions', type='int', dest='dimensions',
        default=1000, help='Number of dimensions.', metavar='NUM')
    parser.add_option('--sigma', type='float', dest='sigma',
        default=0.3, help='Standard deviation of guassian distribution.',
        metavar='FLOAT')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1".'), metavar='FUNCNAME')
    return parser

def getPredictions(dimensions, sigma, reviews1, reviews2):
    predictions = []
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
            rating1 = reviews1[i][2] - bias1
            rating2 = reviews2[j][2] - bias2
            # make prediction
            predictions.append((userId1, rating1, rating2,
                cosineSimSim(dimensions, sigma, rating1, rating2)))
            i += 1
            j += 1
    return predictions

def processPairs(db_conn, inputfile, outputDir, outputTemplate,
                 dimensions, sigma, cosineFunc):
    db_curs = db_conn.cursor()
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
        # get predictions
        predictions = getPredictions(dimensions, sigma, reviews1, reviews2)
        # write output
        outputFileName = os.path.join(outputDir,
            outputTemplate % (productId1, productId2))
        with open(outputFileName, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for (userId, rating1, rating2, prediction) in predictions:
                error = prediction - cosineSim
                writer.writerow([userId, rating1, rating2, prediction, error])

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
    if options.outputDir:
        outputDir = options.outputDir
    else:
        outputDir = options.exptFunc
    if not os.path.isdir(outputDir):
       print >> sys.stderr, 'Cannot find output dir: %s' % outputDir
       return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return

    # Seed random module
    random.seed(options.randomSeed)

    # Connect to db
    print 'Connect to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Open input file
    print 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')

    # Make predictions
    outputTemplate = outputTemplateTemplate % options.cosineFunc
    processPairs(db_conn, inputfile, options.outputDir, outputTemplate,
                 options.dimensions, options.sigma, cosineFunc)
    
if __name__ == '__main__':
    main()
