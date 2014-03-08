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

# params
stepSize = 10
K = 20
sigma = 1.1
workerTimeout = 15
workerQueueSize = 100
outputFileTemplate = '%s_%s_%s.csv'

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
        default=4, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default=None,
        help='Output directory.', metavar='DIR')
    parser.add_option('-p', '--prefix', dest='prefix', default=None,
        help='Output file prefix.', metavar='STR')
    parser.add_option('-e', '--exptFunc', dest='exptFunc', default='expt1',
        help='Experiment function to use: "expt1" (default) or "expt2"',
        metavar='FUNCNAME')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc', default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1"'),
        metavar='FUNCNAME')
    parser.add_option('-s', '--stepSize', dest='stepSize', type='int',
        default=None, help='Step size prefSim or prefSimAlt1.', metavar='NUM')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    return parser

def randSim(reviewsA, reviewsB, biasA, biasB):
    """Compute the "random" similarity between items A and B.
       This similarity function is the cosine similarity that only
       includes ratings by users who have rated both items.
    """
    numUsersCommon = 0
    innerProd = 0
    varA = 0
    varB = 0
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
            numUsersCommon += 1
            scoreA = reviewsA[i][2] - biasA
            scoreB = reviewsB[j][2] - biasB
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
    if innerProd == 0:
        return (0, numUsersCommon)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return (cosineSim, numUsersCommon)

def randSimAlt1(reviewsA, reviewsB, biasA, biasB):
    """Compute the "random" similarity between items A and B.
       This similarity function is the cosine similarity that only
       includes ratings by users who have rated both items.
       Altered Version 1: If the length of a reviews vector is less than K,
           we add (K - len(CommonReviewers))*sigma**2 to its variance as
           used in the cosine similarity function, where K and sigma are
           global parameters.
    """
    numUsersCommon = 0
    innerProd = 0
    varA = 0
    varB = 0
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
            numUsersCommon += 1
            scoreA = reviewsA[i][2] - biasA
            scoreB = reviewsB[j][2] - biasB
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
    # Magical fudge factor
    if numUsersCommon < K:
        varA += (K - numUsersCommon)*sigma**2
        varB += (K - numUsersCommon)*sigma**2
    if innerProd == 0:
        return (0, numUsersCommon)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return (cosineSim, numUsersCommon)

def prefSim(reviewsA, reviewsB, biasA, biasB):
    """Compute the "preferential" similarity between items A and B.
       This similarity function is the cosine similarity that includes
       ratings by users who have rated both items as well as those 
       by users who have rated only one item.
    """
    numUsersCommon = 0
    innerProd = 0
    varA = 0
    varB = 0
    i = 0
    j = 0
    while i < len(reviewsA) and j < len(reviewsB):
        userIdA = reviewsA[i][1]
        userIdB = reviewsB[j][1]
        if userIdA < userIdB:
            scoreA = reviewsA[i][2] - biasA
            varA += scoreA**2
            i += 1
        elif userIdA > userIdB:
            scoreB = reviewsB[j][2] - biasB
            varB += scoreB**2
            j += 1
        else:
            timeA = reviewsA[i][0]
            timeB = reviewsB[j][0]
            if timeA == timeB:
                i += 1
                j += 1
                continue # ignore duplicate reviews
            numUsersCommon += 1
            scoreA = reviewsA[i][2] - biasA
            scoreB = reviewsB[j][2] - biasB
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
    while i < len(reviewsA):
        scoreA = reviewsA[i][2] - biasA
        varA += scoreA**2
        i += 1
    while j < len(reviewsB):
        scoreB = reviewsB[j][2] - biasB
        varB += scoreB**2
        j += 1
    if innerProd == 0:
        return (0, numUsersCommon)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return (cosineSim, numUsersCommon)

def prefSimAlt1(reviewsA, reviewsB, biasA, biasB):
    """Compute the "preferential" similarity between items A and B.
       This similarity function is the cosine similarity that includes
       ratings by users who have rated both items as well as those 
       by users who have rated only one item.
       Altered Version 1: If the length of a reviews vector is less than K,
           we add (K - len(reviews))*sigma**2 to its variance as used in the
           cosine similarity function, where K and sigma are global parameters.
    """
    numUsersCommon = 0
    innerProd = 0
    varA = 0
    varB = 0
    i = 0
    j = 0
    while i < len(reviewsA) and j < len(reviewsB):
        userIdA = reviewsA[i][1]
        userIdB = reviewsB[j][1]
        if userIdA < userIdB:
            scoreA = reviewsA[i][2] - biasA
            varA += scoreA**2
            i += 1
        elif userIdA > userIdB:
            scoreB = reviewsB[j][2] - biasB
            varB += scoreB**2
            j += 1
        else:
            timeA = reviewsA[i][0]
            timeB = reviewsB[j][0]
            if timeA == timeB:
                i += 1
                j += 1
                continue # ignore duplicate reviews
            numUsersCommon += 1
            scoreA = reviewsA[i][2] - biasA
            scoreB = reviewsB[j][2] - biasB
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
    while i < len(reviewsA):
        scoreA = reviewsA[i][2] - biasA
        varA += scoreA**2
        i += 1
    while j < len(reviewsB):
        scoreB = reviewsB[j][2] - biasB
        varB += scoreB**2
        j += 1
    # Magical fudge factor
    if len(reviewsA) < K:
        varA += (K - len(reviewsA))*sigma**2
    if len(reviewsB) < K:
        varB += (K - len(reviewsB))*sigma**2
    if innerProd == 0:
        return (0, numUsersCommon)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return (cosineSim, numUsersCommon)

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
        if j == len(reviews2) or reviews1[i][0] <= reviews2[j][0]:
            i += 1
        elif i == len(reviews1) or reviews1[i][0] > reviews2[j][0]:
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
            # compute product biases
            if pastReviews1:
                bias1 = numpy.mean([review[2] for review in pastReviews1])
            else:
                bias1 = 0.0
            if pastReviews2:
                bias2 = numpy.mean([review[2] for review in pastReviews2])
            else:
                bias2 = 0.0
            # compute cosine similarity at present time slice
            # using the provided function.
            cosineSim, numUserCommon =\
                cosineFunc(pastReviews1, pastReviews2, bias1, bias2)
            # write step info
            writer.writerow([count, i, j, numUserCommon, cosineSim])

def expt2(db_conn, writer, cosineFunc, productId1, productId2):
    db_curs = db_conn.cursor()
    # fetch product reviews
    db_curs.execute(selectReviewsOrderByUserStmt, (productId1,))
    reviews1 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
    db_curs.execute(selectReviewsOrderByUserStmt, (productId2,))
    reviews2 = [(row[0], row[1], row[2]) for row in db_curs.fetchall()]
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
        stepReviews1 = sorted(reviews1[stepBegin_i:i], key=lambda x: x[1])
        stepReviews2 = sorted(reviews2[stepBegin_j:j], key=lambda x: x[1])
        stepBegin_i = i
        stepBegin_j = j
        # append to past reviews and sort by userId
        pastReviews1 = sorted(pastReviews1 + stepReviews1,
                              key=lambda x:x[1])
        assert(pastReviews1)
        pastReviews2 = sorted(pastReviews2 + stepReviews2,
                              key=lambda x:x[1])
        assert(pastReviews2)
        # compute biases
        bias1 = numpy.mean([review[2] for review in pastReviews1])
        bias2 = numpy.mean([review[2] for review in pastReviews2])
        # compute cosine similarity at present time slice
        # using the provided function.
        cosineSim, numUserCommon =\
            cosineFunc(pastReviews1, pastReviews2, bias1, bias2)
        # write step info
        writer.writerow([i+j, i, j, numUserCommon, cosineSim])

def worker(workerIdx, q, db_fname, outputDir, prefix, exptFunc, cosineFunc):
    num_writes = 0
    num_skips = 0
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)

    # TODO: Need a terminal condition here.
    while True:
        (productId1, productId2) = q.get()
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
        cosineFunc = globals()[options.cosineFunc]
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
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
    global K
    if options.K:
        K = options.K
    global sigma
    if options.sigma:
        sigma = options.sigma

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
