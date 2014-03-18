#!/usr/local/bin/python

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import csv
import os
import sys
import random
import numpy as np

import similarity
from cosineSimSim import cosineSimSim

# params
outputTemplateTemplate = '%s_%%s_%%s.csv'
workerTimeout = 20
workerQueueSize = 100
END_OF_QUEUE = -1

# db params
dbTimeout = 5
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-w', '--numWorkers', dest='numWorkers', type='int',
        default=1, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir',
        default='predictions', help='Output directory.', metavar='DIR')
    parser.add_option('--randomSeed', type='int', dest='randomSeed',
        default=0, help='Seed for random module.', metavar='NUM')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help='Similarity function to use: "prefSim" (default) or "randSim"',
              metavar='FUNCNAME')
    parser.add_option('--dimensions', type='int', dest='dimensions',
        default=100, help='Number of dimensions.', metavar='NUM')
    parser.add_option('--sigmaXX', type='float', dest='sigmaXX', default=1.0,
       help=('Diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    parser.add_option('--sigmaXY', type='float', dest='sigmaXY', default=0.3,
       help=('Off-diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    return parser

def getPredictions(dimensions, sigma, reviews1, reviews2):
    assert(sigma.shape == (2, 2))
    predictions = []
    # compute product biases
    bias1 = np.mean([review[2] for review in reviews1])
    bias2 = np.mean([review[2] for review in reviews2])
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
            # make mu vector
            mu = np.array([rating1, rating2])
            # make prediction
            predictions.append((userId1, rating1, rating2,
                               cosineSimSim(dimensions, mu, sigma)))
            i += 1
            j += 1
    return predictions

def processPair(db_conn, writer, dimensions, sigma, cosineFunc,
                productId1, productId2):
    assert(sigma.shape == (2, 2))
    db_curs = db_conn.cursor()
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
    for (userId, rating1, rating2, prediction) in predictions:
        error = prediction - cosineSim
        writer.writerow([userId, rating1, rating2, prediction, error])

def worker(workerIdx, q, db_fname, outputDir, outputTemplate, randomSeed,
           dimensions, sigma, cosineFunc):
    assert(sigma.shape == (2, 2))
    num_writes = 0
    num_skips = 0
    # Seed random module
    random.seed(randomSeed)
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    while True:
        (productId1, productId2) = q.get()
        if productId1 == END_OF_QUEUE: break
        outputFileName = os.path.join(outputDir, outputTemplate %
                                      (productId1, productId2))
        if os.path.isfile(outputFileName):
            num_skips += 1
            print 'Skipping %s . . .' % outputFileName
        else:
            print 'Writing %s . . .' % outputFileName
            with open(outputFileName, 'wb') as csvfile:
                writer = csv.writer(csvfile)
                processPair(db_conn, writer, dimensions, sigma,
                            cosineFunc, productId1, productId2)
                num_writes += 1

def master(inputfile, queues, workers):
    i = 0
    for line in inputfile:
        tokens = line.split(',')
        productId1 = tokens[0].strip()
        productId2 = tokens[1].strip()
        workerIdx = i % len(workers)

        while True:
            try:
                queues[workerIdx].put((productId1, productId2),
                                      timeout=workerTimeout)
                break
            except Queue.Full:
                print 'WARNING: Worker Queue Full!'
        i += 1

    # close queues
    for q in queues:
        q.put((END_OF_QUEUE, END_OF_QUEUE))
        q.close()

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

    outputTemplate = outputTemplateTemplate % options.cosineFunc

    # form sigma matrix
    sigma = np.array([[options.sigmaXX, options.sigmaXY],
                      [options.sigmaXY, options.sigmaXX]])

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        workers.append(mp.Process(target=worker,
            args=(w, queues[w], options.db_fname, outputDir, outputTemplate,
                  options.randomSeed, options.dimensions, sigma, cosineFunc)))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # open input file
    print 'Reading from %s. . .' % inputFileName
    with open(inputFileName, 'r') as inputfile:
        # do master task
        master(inputfile, queues, workers)

if __name__ == '__main__':
    main()
