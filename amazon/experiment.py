#!/usr/local/bin/python

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import numpy as np
import csv
import os
import sys
import math

import similarity
import modelPredictions as modpred

# params
stepSize = 10
workerTimeout = 15
workerQueueSize = 100
outputFileTemplate = '%s_%s_%s.csv'
END_OF_QUEUE = -1

#db params
dbTimeout = 5
selectReviewsOrderByTimeStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY Time')
selectReviewsOrderByUserStmt =\
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
    parser.add_option('-o', '--output-dir', dest='outputDir', default=None,
        help='Output directory.', metavar='DIR')
    parser.add_option('-p', '--prefix', dest='prefix', default=None,
        help='Output file prefix.', metavar='STR')
    parser.add_option('-e', '--exptFunc', dest='exptFunc', default='expt1',
        help='Experiment function to use: "expt1" (default) or "expt2"',
        metavar='FUNCNAME')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", "randSimAlt1", "regSim", "momSim", "alphaSim" or "predSim"'),
        metavar='FUNCNAME')
    parser.add_option('--regSimRawFunc', dest='regSimRawFunc',
        default='randSim',
        help=('Similarity function to used for raw similarity by regSim: '
              '"prefSim", or "randSim" (default)'), metavar='FUNCNAME')
    parser.add_option('--momSimRawFunc', dest='momSimRawFunc',
        default='randSim',
        help=('Similarity function to used for raw similarity by momSim: '
              '"prefSim", or "randSim" (default)'), metavar='FUNCNAME')
    parser.add_option('--alphaSimRawFunc', dest='alphaSimRawFunc',
        default='randSim',
        help=('Similarity function to used for raw similarity by alphaSim: '
              '"prefSim", or "randSim" (default)'), metavar='FUNCNAME')
    parser.add_option('--regSimParamsFile', dest='regSimParamsFile',
        default='output/regSim_params.csv', help='Parameter file for regSim.',
        metavar='FILE')
    parser.add_option('--momSimParamsFile', dest='momSimParamsFile',
        default='output/momSim_params.csv', help='Parameter file for momSim.',
        metavar='FILE')
    parser.add_option('--alphaSimParamsFile', dest='alphaSimParamsFile',
        default='output/alphaSim_params.csv', help='Parameter file for alphaSim.',
        metavar='FILE')
    parser.add_option('--max-common-reviewers', dest='maxUsersCommon',
        type='int', default=100,
        help='Maximum number of common reviewers for regSim, momSim, or alphaSim.', metavar='NUM')
    parser.add_option('--simGridFile', dest='simGridFile',
        default='output/simGrid_randSim.csv',
        help='CSV containing simGrid data.', metavar='FILE')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-2.0, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=2.0, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.1, help='Step rating.', metavar='FLOAT')
    parser.add_option('-s', '--stepSize', dest='stepSize', type='int',
        default=None, help='Step size prefSim or prefSimAlt1.', metavar='NUM')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    parser.add_option('--errorFileName', dest='errorFileName',
        default='output/aggregatePredictions_modelSim_2.2_0.5_0.3.csv',
        help='User prediction errors file for modelSim.', metavar='FILE')
    parser.add_option('--epsilon', dest='epsilon', type='float', default=0.5,
        help='Parameter epsilon for weightedRandSim or wightedPrefSim.',
        metavar='FLOAT')
    return parser

def getReviewPairTimes(reviewsA, reviewsB):
    reviewPairTimes = []
    i = 0
    j = 0
    while i < len(reviewsA) and j < len(reviewsB):
        userIdA = reviewsA[i][1]
        userIdB = reviewsB[j][1]
        if userIdA < userIdB:
            i += 1
        elif userIdA > userIdB:
            j += 1
        else:
            timeA = reviewsA[i][0]
            timeB = reviewsB[j][0]
            if timeA == timeB:
                i += 1
                j += 1
                continue # ignore duplicate reviews
            reviewPairTimes.append(max(timeA, timeB))
            i += 1
            j += 1
    return reviewPairTimes

def expt1(db_conn, writer, cosineFunc, productId1, productId2):
    db_curs = db_conn.cursor()
    # fetch product reviews
    db_curs.execute(selectReviewsOrderByTimeStmt, (productId1,))
    reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    db_curs.execute(selectReviewsOrderByTimeStmt, (productId2,))
    reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    i = 0
    j = 0
    stepBegin_i = 0
    stepBegin_j = 0
    pastReviews1 = []
    pastReviews2 = []
    count = 0
    # TODO: Fix so that we capture the last (partial) step.
    while i < len(reviews1) or j < len(reviews2):
        if j == len(reviews2) or\
          (i < len(reviews1) and reviews1[i][0] <= reviews2[j][0]):
            i += 1
        elif i == len(reviews1) or\
            (j < len(reviews2) and reviews1[i][0] > reviews2[j][0]):
            j += 1
        else:
            raise RuntimeError('Unreachable code.')
        count += 1
        if count % stepSize == 0:
            # extract reviews for step and sort by userId
            # (faster to pre-sort step)
            stepReviews1 = sorted(reviews1[stepBegin_i:i], key=lambda x: x[1])
            stepReviews2 = sorted(reviews2[stepBegin_j:j], key=lambda x: x[1])
            stepBegin_i = i
            stepBegin_j = j
            # append to past reviews and sort by userId
            pastReviews1 = sorted(pastReviews1 + stepReviews1,
                                  key=lambda x:x[1])
            pastReviews2 = sorted(pastReviews2 + stepReviews2,
                                  key=lambda x:x[1])
            # compute cosine similarity at present time slice
            # using the provided function.
            cosineSim, numUserCommon =\
                cosineFunc(pastReviews1, pastReviews2)
            # write step info
            writer.writerow([count, i, j, numUserCommon, cosineSim])

def expt2(db_conn, writer, cosineFunc, productId1, productId2):
    db_curs = db_conn.cursor()
    # fetch product reviews
    db_curs.execute(selectReviewsOrderByUserStmt, (productId1,))
    reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    db_curs.execute(selectReviewsOrderByUserStmt, (productId2,))
    reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    # compute product biases
    bias1 = np.mean([review[2] for review in reviews1])
    bias2 = np.mean([review[2] for review in reviews2])
    # determine review pair times
    reviewPairTimes = getReviewPairTimes(reviews1, reviews2)
    # sort everything by time
    reviewPairTimes.sort()
    reviews1 = sorted(reviews1, key=lambda x: x[0])
    reviews2 = sorted(reviews2, key=lambda x: x[0])
    # iterate over review pairs
    stepBegin_i = 0
    stepBegin_j = 0
    pastReviews1 = []
    pastReviews2 = []
    predReviews1 = []
    predReviews2 = []
    predictions = []
    i = 0
    j = 0
    for pairTime in reviewPairTimes:
        # advance review indexes
        while (i < len(reviews1)):
            if (reviews1[i][0] > pairTime):
                break
            i += 1
        while (j < len(reviews2)):
            if (reviews2[j][0] > pairTime):
                break
            j += 1
        # sort reviews by userId
        stepReviews1 = sorted(reviews1[stepBegin_i:i], key=lambda x: x[1])
        stepReviews2 = sorted(reviews2[stepBegin_j:j], key=lambda x: x[1])
        stepBegin_i = i
        stepBegin_j = j
        # special handling for modelSim
        if cosineFunc == similarity.modelSim or\
           cosineFunc == similarity.weightedModelSim:
            predReviews1 =\
                sorted(predReviews1 + stepReviews1, key=lambda x: x[1])
            predReviews2 =\
                sorted(predReviews2 + stepReviews2, key=lambda x: x[1])
            predictions += modpred.getPredictions(predReviews1, predReviews2,
                                                  bias1, bias2)
            # remove predictors from predReviews to avoid double counting
            predReviews1 = [r for r in predReviews1\
                            if r[1] not in [p[0] for p in predictions]]
            predReviews2 = [r for r in predReviews2\
                            if r[1] not in [p[0] for p in predictions]]
            # compute weighted mean
            totalScore = 0
            totalWeight = 0
            for p in predictions:
                if cosineFunc == similarity.weightedModelSim:
                    try:
                        weight = similarity.weights[p[0]]
                    except:
                        weight = similarity.avgWeight
                else:
                    weight = 1
                totalScore += p[3]*weight
                totalWeight += weight
            cosineSim = totalScore/totalWeight
            numUserCommon = len(predictions)
        else:
            # append to past reviews and sort by userId
            pastReviews1 = sorted(pastReviews1 + stepReviews1,
                                  key=lambda x: x[1])
            assert(pastReviews1)
            pastReviews2 = sorted(pastReviews2 + stepReviews2,
                                  key=lambda x: x[1])
            assert(pastReviews2)
            # compute cosine similarity at present time slice
            # using the provided function.
            cosineSim, numUserCommon = cosineFunc(pastReviews1, pastReviews2)
        # write step info
        writer.writerow([i+j, i, j, numUserCommon, cosineSim])

def worker(workerIdx, q, db_fname, outputDir, prefix, exptFunc, cosineFunc):
    num_writes = 0
    num_skips = 0
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    while True:
        (productId1, productId2) = q.get()
        if productId1 == END_OF_QUEUE: break
        outputFileName = os.path.join(outputDir, outputFileTemplate %
                                      (prefix, productId1, productId2))
        if os.path.isfile(outputFileName):
            num_skips += 1
            print 'Skipping %s . . .' % outputFileName
        else:
            print 'Writing %s . . .' % outputFileName
            with open(outputFileName, 'wb') as csvfile:
                writer = csv.writer(csvfile)
                exptFunc(db_conn, writer, cosineFunc, productId1, productId2)
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
    try:
        exptFunc = globals()[options.exptFunc]
    except KeyError:
        print >> sys.stderr,\
            'Invalid Experiment function: %s' % options.exptFunc
        return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return
    try:
        regSimRawFunc = getattr(similarity, options.regSimRawFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Raw Similarity function: %s' % options.regSimRawFunc
        return
    try:
        momSimRawFunc = getattr(similarity, options.momSimRawFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Raw Similarity function: %s' % options.momSimRawFunc
        return
    try:
        alphaSimRawFunc = getattr(similarity, options.alphaSimRawFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Raw Similarity function: %s' % options.alphaSimRawFunc
        return
    if options.outputDir:
        outputDir = options.outputDir
    else:
        outputDir = options.exptFunc
    if not os.path.isdir(outputDir):
       print >> sys.stderr, 'Cannot find output dir: %s' % outputDir
       return
    if options.prefix:
        prefix = options.prefix
    else:
        prefix = options.cosineFunc
    global stepSize
    if options.stepSize:
        stepSize = options.stepSize
    if options.K:
        similarity.K = options.K
    if options.sigma:
        similarity.sigma = options.sigma

    # regSim
    if options.cosineFunc == 'regSim':
        similarity.initRegSim(options.regSimParamsFile, regSimRawFunc,
                   options.maxUsersCommon)

    # momSim
    if options.cosineFunc == 'momSim':
        similarity.initMomSim(options.momSimParamsFile, momSimRawFunc,
                   options.maxUsersCommon)

    # alphaSim
    if options.cosineFunc == 'alphaSim':
        similarity.initMomSim(options.alphaSimParamsFile, alphaSimRawFunc,
                   options.maxUsersCommon)

    # predSim
    if options.cosineFunc == 'predSim':
        similarity.initPredSim(options.minRating, options.maxRating,
                               options.stepRating, options.simGridFile)

    # weighted similarity
    if options.cosineFunc == 'weightedModelSim':
        similarity.initWeightedSim(options.errorFileName, options.epsilon)

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        workers.append(mp.Process(target=worker,
            args=(w, queues[w], options.db_fname, outputDir, prefix,
                  exptFunc, cosineFunc)))

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
