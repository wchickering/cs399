#!/usr/local/bin/python

"""
Creates edge records with cosine similarities and number of common users
as per user-item collaborative filtering.
"""

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import csv
import os
import math

# params
workerTimeout = 30
workerQueueSize = 1000

# db params
dbTimeout = 5
selectGlobalBiasStmt = 'SELECT Value FROM Globals WHERE Key = "Bias"'
selectReviewsStmt =\
    ('SELECT R.UserId, R.Score - PB.Bias - UB.Bias, Time, Summary '
     'FROM Reviews AS R, ProductBiases AS PB, UserBiases AS UB '
     'WHERE R.ProductId = PB.ProductId '
     'AND R.UserId = UB.UserId '
     'AND R.ProductId = :ProductId '
     'ORDER BY R.UserId')


def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='data/amazon.db',
        help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default='data',
        help='Output directory.', metavar='DIR')
    parser.add_option('-w', '--numWorkers', dest='numWorkers', type='int',
        default=4, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-m', '--minUsers', dest='minUsers', type='int',
        default=1, help='Minimum number of users for a similarity.', metavar='NUM')
    return parser


def computeSim(reviewsA, reviewsB):
    """Compute Cosine similarity of sparse vectors in O(n),
       where n is the max nonzero elements of the two vectors.
    """
    numUsers = 0
    innerProd = 0
    varA = 0
    varB = 0
    i = 0
    j = 0
    while i < len(reviewsA) and j < len(reviewsB):
        userIdA = reviewsA[i][0]
        userIdB = reviewsB[j][0]
        if userIdA < userIdB:
            scoreA = reviewsA[i][1]
            varA += scoreA**2
            i += 1
        elif userIdA > userIdB:
            scoreB = reviewsB[j][1]
            varB += scoreB**2
            j += 1
        else:
            timeA = reviewsA[i][2]
            timeB = reviewsB[j][2]
            if timeA == timeB:
                summaryA = reviewsA[i][3]
                summaryB = reviewsB[j][3]
                if summaryA == summaryB:
                    i += 1
                    j += 1
                    continue # ignore duplicate reviews
            numUsers += 1
            scoreA = reviewsA[i][1]
            scoreB = reviewsB[j][1]
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
    if innerProd == 0:
        return (0, numUsers)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return (cosineSim, numUsers)


def worker(workerIdx, q, db_fname, minUsers, outputFileName):
    num_writes = 0
    num_skips = 0
    # connect to db
    db_conn = sqlite3.connect(db_fname, dbTimeout)
    db_curs = db_conn.cursor()
    # Retrieve the global bias
    db_curs.execute(selectGlobalBiasStmt)
    globalBias = float(db_curs.fetchone()[0])

    print 'Writing to %s . . .' % outputFileName
    with open(outputFileName, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        # TODO: Need a terminal condition here.
        while True:
            (productId1, productId2) = q.get()
            db_curs.execute(selectReviewsStmt, (productId1,))
            reviews1 = [(row[0], row[1] - globalBias, row[2], row[3])\
                        for row in db_curs.fetchall()]
            db_curs.execute(selectReviewsStmt, (productId2,))
            reviews2 = [(row[0], row[1] - globalBias, row[2], row[3])\
                        for row in db_curs.fetchall()]
            cosineSim, numUsers = computeSim(reviews1, reviews2)
            if numUsers < minUsers:
                num_skips += 1
                continue # skip when below minUsers threshold
            if cosineSim == 0:
                num_skips += 1
                continue # skip zero similarity edges
            writer.writerow([productId1, productId2, cosineSim, numUsers])
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
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        outputFileName = os.path.join(options.outputDir,
            '%s_%d.out' % (os.path.splitext(os.path.basename(__file__))[0], w))
        workers.append(mp.Process(target=worker,
            args=(w, queues[w], options.db_fname, options.minUsers,
                  outputFileName)))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # open input file
    print 'Reading from %s. . .' % inputfilename
    with open(inputfilename, 'r') as inputfile:
        # do master task
        master(inputfile, queues, workers)

if __name__ == '__main__':
    main()
