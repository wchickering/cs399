#!/usr/local/bin/python

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import csv
import os

# params
workerTimeout = 10
workerQueueSize = 100
outputFileTemplate = '%s_%d.csv'

# db params
dbTimeout = 5
selectReviewsStmt =\
    ('SELECT UserId, Time, Score '
     'FROM Reviews '
     'ORDER BY UserId, Time')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default='output',
        help='Output directory.', metavar='DIR')
    parser.add_option('-w', '--numWorkers', dest='numWorkers', type='int',
        default=1, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-p', '--prefix', dest='prefix', default=None,
        help='Output file prefix.', metavar='STR')
    return parser

def worker(workerIdx, q, outputDir, prefix):
    num_writes = 0
    outputFileName = os.path.join(outputDir,
                                  outputFileTemplate % (prefix, workerIdx))
    print 'Witing %s . . .' % outputFileName
    with open(outputFileName, 'wb') as csvfile:
        writer = csv.writer(csvfile)

        # TODO: Need a terminal condition here.
        lastUserId = None
        firstTime = None
        while True:
            row = q.get()
            userId = row[0]
            time = row[1]
            score = row[2]
            if userId != lastUserId:
                lastUserId = userId
                firstTime = time
            duration = time - firstTime
            writer.writerow([duration, score])
            num_writes += 1

def master(db_conn, queues, workers):
    db_curs = db_conn.cursor()
    db_curs.execute(selectReviewsStmt)
    userCnt = 0
    lastUserId = None
    while True:
        row = db_curs.fetchone()
        if row is None:
            break
        userId = row[0]
        if userId != lastUserId:
            print 'Processing userId: %s' % userId
            lastUserId = userId
            userCnt += 1
        workerIdx = userCnt % len(workers)

        while True:
            try:
                queues[workerIdx].put(row, timeout=workerTimeout)
                break
            except Queue.Full:
                print 'WARNING: Worker Queue Full!'

    # close queues
    for q in queues:
        q.close()

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.prefix:
        prefix = options.prefix
    else:
        prefix = os.path.splitext(os.path.basename(__file__))[0]

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        workers.append(mp.Process(target=worker,
            args=(w, queues[w], options.outputDir, prefix)))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # connect to db
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)
    
    # do master task
    master(db_conn, queues, workers)

if __name__ == '__main__':
    main()
