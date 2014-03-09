#!/usr/local/bin/python

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import csv
import os
import sys
import math
import numpy
import random

import similarity

# params
randomSeed = 0
workerTimeout = 30
workerQueueSize = 1000
outputFileTemplate = '%s_%d.csv'
END_OF_QUEUE = -1

#db params
dbTimeout = 5
selectProductsStmt = 'SELECT ProductId FROM Products'
selectTargetsStmt =\
    ('SELECT  UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId ')
selectNeighborsStmt =\
    ('SELECT ProductId2 as ProductId '
     'FROM Neighbors '
     'WHERE ProductId1 = :ProductId1 '
     'UNION '
     'SELECT ProductId1 as ProductId '
     'FROM Neighbors '
     'WHERE ProductId2 = :ProductId2 ')
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
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc', default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1"'),
        metavar='FUNCNAME')
    parser.add_option('--productSampleRate', dest='productSampleRate', type='float',
        default=0.01, help='Fraction of products to predict review scores for.',
        metavar='FLOAT')
    parser.add_option('--reviewSampleRate', dest='reviewSampleRate', type='float',
        default=0.1, help='Fraction of review scores to predict.', metavar='FLOAT')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    return parser

def doExperiment(db_conn, csvfile, cosineFunc, reviewSampleRate, targetProductId):
    count = 0
    skips = 0
    totalError = 0
    totalSquaredError = 0
    writer = csv.writer(csvfile)
    # get the neighbors
    db_curs = db_conn.cursor()
    db_curs.execute(selectNeighborsStmt, (targetProductId, targetProductId))
    neighbors = db_curs.fetchall()
    if not neighbors:
        #print 'No neighbors for %s.' % targetProductId
        return 0
    # get target reviews
    db_curs.execute(selectReviewsStmt, (targetProductId,))
    targetReviews = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    if not targetReviews:
        print 'No target reviews for %s.' % targetProductId
        return 0
    # get prediction targets
    db_curs.execute(selectTargetsStmt, (targetProductId,))
    while True:
        row = db_curs.fetchone()
        if not row:
            break
        # decide whether to sample target
        if random.random() >= reviewSampleRate:
            skips += 1
            continue
        targetUserId = row[0]
        targetAdjustedScore = row[1]
        # exclude targetUserId from targetReviews
        targetReviewsPrime = [review for review in targetReviews\
                                     if review[1] != targetUserId]
        assert(targetReviewsPrime)
        # compute bias associated with target product
        targetBias = numpy.mean([review[2] for review in targetReviewsPrime])
        #compute the target score
        targetScore = targetAdjustedScore - targetBias
        # retrieve neighbors
        weights = []
        scores = []
        for row in neighbors:
            productId = row[0]
            # retrieve reviews of neighbor
            db_curs1 = db_conn.cursor()
            db_curs1.execute(selectReviewsStmt, (productId,))
            reviews = [(row[0], row[1], row[2]) for row in db_curs1.fetchall()]
            if not reviews:
                print 'WARNING: No reviews for neighbor: %s.' % productId
                continue
            # check for target userId
            proxyList = [row for row in reviews if row[1] == targetUserId]
            if not proxyList:
                continue
            assert(len(proxyList) == 1)
            # compute bias
            bias = numpy.mean([review[2] for review in reviews])
            # compute proxy score
            proxyScore = proxyList[0][2] - bias
            # compute cosine similarity at present time slice
            # using the provided function.
            cosineSim, numUserCommon =\
                cosineFunc(targetReviewsPrime, reviews, targetBias, bias)
            if cosineSim > 0.0:
                weights.append(cosineSim)
                scores.append(proxyScore)
        if not weights: continue
        # make prediction and print error
        count += 1
        total = 0
        for i in range(len(weights)):
            total += weights[i]*scores[i]
        prediction = total/sum(weights)
        error = float(prediction) - float(targetScore)
        squaredError = error**2
        totalError += error
        totalSquaredError += squaredError
        writer.writerow([targetProductId, targetUserId, targetScore,
                         prediction, len(weights)])
        csvfile.flush()
    if count == 0:
        #print 'No scores sampled for %s.' % targetProductId
        return 0
    # Print stats
    #avgError = totalError/count
    #avgSquaredError = totalSquaredError/count
    #print '-------------------------------'
    #print 'targetProductId = %s' % targetProductId
    #print '          count = %d' % count
    #print '          skips = %d' % skips
    #print '        <error> = %0.3f' % avgError
    #print '      <error^2> = %0.3f' % avgSquaredError
    return count

def worker(workerIdx, q, db_fname, outputDir, cosineFunc, reviewSampleRate):
    # seed random number generator
    random.seed(randomSeed)
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    # open output file
    outputFileName = os.path.join(outputDir, outputFileTemplate %
                                  (cosineFunc.__name__, workerIdx))
    print 'Writing %s . . .' % outputFileName
    with open(outputFileName, 'wb') as csvfile:
        predictions = 0
        products = 0
        zeros = 0
        while True:
            targetProductId = q.get()
            if targetProductId == END_OF_QUEUE:
                break
            c = doExperiment(db_conn, csvfile, cosineFunc,
                             reviewSampleRate, targetProductId)
            if c > 0:
                products += 1
            else:
                zeros += 1
            predictions += c
    # Print stats
    print '==========================='
    print 'Made %d predictions for %d products.' % (predictions, products)
    print '(%d products skipped b/c no neighbors)' % zeros
                

def master(db_fname, queues, workers, productSampleRate):
    # seed random number generator
    random.seed(randomSeed)
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    db_curs = db_conn.cursor()
    db_curs.execute(selectProductsStmt)
    i = 0
    while True:
        row = db_curs.fetchone()
        if not row: break
        if random.random() >= productSampleRate: continue
        targetProductId = row[0]
        workerIdx = i % len(workers)
        while True:
            try:
                queues[workerIdx].put(targetProductId, timeout=workerTimeout)
                break
            except Queue.Full:
                print 'WARNING: Worker Queue Full!'
        i += 1

    # close queues
    for q in queues:
        q.put(END_OF_QUEUE)
        q.close()

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return
    if not os.path.isdir(options.outputDir):
       print >> sys.stderr, 'Cannot find output dir: %s' % options.outputDir
       return
    if options.K:
        similarity.K = options.K
    if options.sigma:
        similarity.sigma = options.sigma

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        workers.append(mp.Process(target=worker,
            args=(w, queues[w], options.db_fname, options.outputDir,
                  cosineFunc, options.reviewSampleRate)))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # do master task
    master(options.db_fname, queues, workers, options.productSampleRate)

if __name__ == '__main__':
    main()
