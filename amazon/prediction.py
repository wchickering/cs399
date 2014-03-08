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
workerTimeout = 15
workerQueueSize = 100
outputFileTemplate = '%s_%s.csv'
END_OF_QUEUE = -1

#db params
dbTimeout = 5
selectTargetsStmt =\
    ('SELECT  UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId ')
selectNeighborsStmt =\
    ('SELECT ProductId2 as ProductId '
     'FROM Similarities '
     'WHERE ProductId1 = :ProductId1 '
     'UNION '
     'SELECT ProductId1 as ProductId '
     'FROM Similarities '
     'WHERE ProductId2 = :ProductId2 ')
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-w', '--numWorkers', dest='numWorkers', type='int',
        default=4, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir',
        default='predictions', help='Output directory.', metavar='DIR')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc', default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1"'),
        metavar='FUNCNAME')
    parser.add_option('-s', '--sampleRate', dest='sampleRate', type='float',
        default=1.0, help='Fraction of ratings to predict.', metavar='FLOAT')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    return parser

def doExperiment(db_conn, csvfile, cosineFunc, sampleRate, targetProductId):

    writer = csv.writer(csvfile)
    db_curs = db_conn.cursor()

    # get the neighbors
    db_curs.execute(selectNeighborsStmt, (targetProductId, targetProductId))
    neighbors = db_curs.fetchall()
    assert(neighbors)

    # get target reviews
    db_curs.execute(selectReviewsStmt, (targetProductId,))
    targetReviews = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    assert(targetReviews)

    # get prediction targets
    count = 0
    skips = 0
    totalError = 0
    totalSquaredError = 0
    db_curs.execute(selectTargetsStmt, (targetProductId,))
    while True:
        row = db_curs.fetchone()
        if not row:
            break
        # decide whether to sample target
        if random.random() > sampleRate:
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
            assert(reviews)
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
        writer.writerow([targetUserId, targetScore, prediction, len(weights)])
        csvfile.flush()

        #print '-------------------------'
        #print '    UserId: %s' % targetUserId
        #print 'True Score: %0.3f' % targetScore
        #print 'Prediction: %0.3f' % prediction
        #print '     Error: %0.3f' % error
        #print '   Error^2: %0.3f' % squaredError
        #sys.stdout.flush()

    # Print stats
    avgError = totalError/count
    avgSquaredError = totalSquaredError/count
    print '-------------------------------'
    print 'targetProductId = %s' % targetProductId
    print '          count = %d' % count
    print '          skips = %d' % skips
    print '        <error> = %0.3f' % avgError
    print '      <error^2> = %0.3f' % avgSquaredError

def worker(workerIdx, q, db_fname, outputDir, cosineFunc, sampleRate):
    # seed random number generator
    random.seed(randomSeed)
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    num_writes = 0
    num_skips = 0
    while True:
        targetProductId = q.get()
        if targetProductId == END_OF_QUEUE:
            break
        outputFileName = os.path.join(outputDir, outputFileTemplate %
                                      (targetProductId, cosineFunc.__name__))
        if os.path.isfile(outputFileName):
            num_skips += 1
            print 'Skipping %s . . .' % outputFileName
        else:
            print 'Writing %s . . .' % outputFileName
            with open(outputFileName, 'wb') as csvfile:
                doExperiment(db_conn, csvfile, cosineFunc, sampleRate,
                             targetProductId)
                num_writes += 1

def master(inputfile, db_fname, queues, workers):
    i = 0
    for line in inputfile:
        targetProductId = line.strip()
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
                  cosineFunc, options.sampleRate)))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # open input file
    print 'Reading from %s. . .' % inputFileName
    with open(inputFileName, 'r') as inputfile:
        # do master task
        master(inputfile, options.db_fname, queues, workers)

if __name__ == '__main__':
    main()
