#!/usr/local/bin/python

"""
Emits product pairs with non-zero cosime similarity as per
user-item collaborative filtering.

This script produces one or more .out files. The idea is to then
concatenate, sort, and remove duplicate pairs. This can be done with
the following commands:
cat *.out > allPairs.out
sort allPairs.out > allPairs_sort.out
uniq allPairs_sort.out > allPairs_uniq.out

The script edgeIngest.py can then be used to compute similarity
scores and insert edge relations into the database.
"""

import multiprocessing as mp
import Queue
from optparse import OptionParser
import sqlite3
import os

# params
workerTimeout = 30
workerQueueSize = 100

# db params
createIndexStmt = 'CREATE INDEX IF NOT EXISTS Reviews_UserId_Idx ON Reviews(UserId)'
selectUsersStmt = 'SELECT UserId FROM Users'
selectReviewsStmt =\
    'SELECT ProductId FROM Reviews WHERE UserId = :UserId ORDER BY ProductId'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='data/amazon.db',
        help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-w', '--numWorkers', dest='numWorkers', type='int',
        default=4, help='Number of worker processes.', metavar='NUM')
    parser.add_option('-p', '--outfilePrefix', dest='outfilePrefix',
        default='nonzeroSims_', help='Prefix of output files.', metavar='PREFIX')
    parser.add_option('-o', '--outfileDir', dest='outfileDir',
        default='data', help='Output directory.', metavar='DIR')
    return parser

def worker(db_fname, outfilename, q):
    # open output file
    outfile = open(outfilename, 'w')
    # connect to db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()

        # TODO: Need a terminal condition here.
        while True:
            userId = q.get()
            db_curs.execute(selectReviewsStmt, (userId,))
            productIds = [row[0] for row in db_curs.fetchall()]
            for i in range(len(productIds)-1):
                for j in range(i+1, len(productIds)):
                    print >> outfile, '%s, %s' % (productIds[i], productIds[j])

def master(db_conn, queues, workers):
    db_curs1 = db_conn.cursor()
    db_curs1.execute(selectUsersStmt)
    i = 0
    for row1 in db_curs1.fetchall():
        userId = row1[0]
        workerIdx = i % len(workers)
        while True:
            try:
                queues[workerIdx].put(userId, timeout=workerTimeout)
                break
            except Queue.Full:
                print 'WARNING: Worker Queue Full!'
        i += 1

    # close queues
    for q in queues:
        q.close()

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # create queues
    queues = []
    for w in range(options.numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(options.numWorkers):
        outfilename = os.path.join(options.outfileDir, 
                                   options.outfilePrefix + str(w) + '.out')
        workers.append(mp.Process(target=worker,
            args=(options.db_fname, outfilename, queues[w])))

    # start worker processes
    for w in range(options.numWorkers):
        workers[w].start()

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create index if not already exists
        db_curs.execute(createIndexStmt)
        # do master task
        master(db_conn, queues, workers)

if __name__ == '__main__':
    main()
