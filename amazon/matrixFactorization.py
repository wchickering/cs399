#!/usr/local/bin/python

from optparse import OptionParser
import sqlite3
import pickle
import numpy as np
import math
import os
import sys

# params
innerDimension = 100
iterations = 40
learningRate = 0.05
regularization = 0.01
displayInterval = 100000

#db params
dbTimeout = 5

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-s', '--save-dir', dest='saveDir',
        default='.mf', help='Save directory.', metavar='DIR')
    parser.add_option('--shuffle', type='int', dest='shuffle', default=0,
        help=('Whether or not to shuffle ratings between each iteration. '
              '1=true, 0=false (default).'), metavar='NUM')
    return parser

def getIdDict(values):
    idDict = {}
    for i in range(len(values)):
        idDict[values[i]] = i
    return idDict

def getUserIdDict(db_conn, userIdDictFilename):
    """Construct UserId dict if not exists"""
    selectUsersStmt = 'SELECT UserId FROM Users'
    db_curs = db_conn.cursor()
    if not os.path.isfile(userIdDictFilename):
        print 'Constructing UserId dict . . .'
        db_curs.execute(selectUsersStmt)
        userIds = [row[0] for row in db_curs.fetchall()]
        userIdDict = getIdDict(userIds)
        pickle.dump(userIdDict, open(userIdDictFilename, 'wb'))
    else:
        print 'Loading UserId dict from %s . . .' % userIdDictFilename
        userIdDict = pickle.load(open(userIdDictFilename, 'rb'))
        print '%d UserIds read' % len(userIdDict)
    return userIdDict

def getProductIdDict(db_conn, productIdDictFilename):
    """Construct ProductId dict if not exists"""
    selectProductsStmt = 'SELECT ProductId FROM Products'
    db_curs = db_conn.cursor()
    if not os.path.isfile(productIdDictFilename):
        print 'Constructing ProductId dict . . .'
        db_curs.execute(selectProductsStmt)
        productIds = [row[0] for row in db_curs.fetchall()]
        productIdDict = getIdDict(productIds)
        pickle.dump(productIdDict, open(productIdDictFilename, 'wb'))
    else:
        print 'Loading ProductId dict from %s . . .' % productIdDictFilename
        productIdDict = pickle.load(open(productIdDictFilename, 'rb'))
        print '%d ProductIds read' % len(productIdDict)
    return productIdDict

def loadMatrix(MFilename):
    return np.load(open(MFilename, 'rb'))

def saveMatrix(M, MFilename):
    np.save(open(MFilename, 'wb'), M)

def SGD_iter(db_curs, productIdDict, userIdDict,
             Q, P, learningRate, regularization, displayInterval):
    cnt = 0
    totalError = 0
    totalSquareError = 0
    while True:
        row = db_curs.fetchone()
        if not row: break
        try:
            # get indices and rating
            i = productIdDict[row[0]]
            u = userIdDict[row[1]]
            r_ui = row[2]
        except:
            print >> sys.stderr,\
                'Exception for ProductId: %s, UserId: %s' % (row[0], row[1])
            raise
        try:
            # compute error
            e_ui = r_ui - np.dot(Q[i,:], P[u,:])
            totalError += e_ui
            totalSquareError += e_ui**2
            # update column vectors
            Q[i,:] =\
                Q[i,:] + learningRate*(e_ui*P[u,:] - regularization*Q[i,:])
            P[u,:] =\
                P[u,:] + learningRate*(e_ui*Q[i,:] - regularization*P[u,:])
        except:
            print >> sys.stderr,\
                'Exception for i = %d, u = %d' % (i, u)
            raise
        cnt += 1
        if cnt % displayInterval == 0:
            print 'Processed %d ratings' % cnt
    return Q, P, cnt, totalError, totalSquareError

def doSGD(db_conn, Q, P, productIdDict, userIdDict, shuffle=False):
    # Run stochastic gradient descent using Reviews
    print 'Running stochastic gradient descent . . .'
    selectReviewsStmt =\
        ('SELECT ProductId, UserId, UnbiasedScore '
         'FROM Reviews LIMIT 100000')
    selectReviewsRandomizedStmt =\
        ('SELECT ProductId, UserId, UnbiasedScore '
         'FROM (SELECT ProductId, UserId, UnbiasedScore '
         'FROM Reviews LIMIT 100000) '
         'ORDER BY random()')
    db_curs = db_conn.cursor()
    for iteration in range(iterations):
        # Unnecessary to randomize on first iteration.
        if iteration == 0 or not shuffle:
            print 'Executing Query . . .'
            db_curs.execute(selectReviewsStmt)
        else:
            print 'Executing Randomized Query . . .'
            db_curs.execute(selectReviewsRandomizedStmt)
        print 'SGD iteration %d . . .' % (iteration + 1)
        try:
            Q, P, cnt, totalError, totalSquareError =\
                SGD_iter(db_curs, productIdDict, userIdDict,
                         Q, P, learningRate, regularization, displayInterval)
        except:
            errMsg = sys.exc_info()[0]
            print >> sys.stderr, 'Error during SGD: %s' % errMsg
            return Q, P
        # Print iteration stats
        avgError = totalError/cnt
        stdError = math.sqrt(totalSquareError/(cnt - 1))
        print '<error> = %0.4f +/- %0.4f' % (avgError, stdError)

    return Q, P

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.shuffle:
        shuffle = True
    else:
        shuffle = False

    # Connect to db
    print 'Connecting to %s . . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)

    # Create save directory if not exists
    if not os.path.exists(options.saveDir):
        os.makedirs(options.saveDir)

    # Get productId dict
    productIdDictFilename = os.path.join(options.saveDir,
                                         'productIdDict.pickle')
    productIdDict = getProductIdDict(db_conn, productIdDictFilename)

    # Get userId dict
    userIdDictFilename = os.path.join(options.saveDir, 'userIdDict.pickle')
    userIdDict = getUserIdDict(db_conn, userIdDictFilename)

    QFilename = os.path.join(options.saveDir, 'Q.pickle')
    PFilename = os.path.join(options.saveDir, 'P.pickle')
    if not os.path.isfile(QFilename) or not os.path.isfile(PFilename):
        # Initialize matrix elements uniformly at random between -0.1 and +0.1.
        print 'Initializing matrices . . .'
        Q = (np.random.rand(len(productIdDict), innerDimension) - 1)/5
        P = (np.random.rand(len(userIdDict), innerDimension) - 1)/5
    else:
        print 'Loading Q Matrix from %s . . .' % QFilename
        Q = loadMatrix(QFilename);
        print 'Loading P Matrix from %s . . .' % PFilename
        P = loadMatrix(PFilename);
    try:
        # Do SGD
        Q, P = doSGD(db_conn, Q, P, productIdDict, userIdDict, shuffle=shuffle)
    finally:
        if P is not None and Q is not None:
            # Save Q and P
            print 'Saving Q Matrix to %s . . .' % QFilename
            saveMatrix(Q, QFilename)
            print 'Saving P Matrix to %s . . .' % PFilename
            saveMatrix(P, PFilename)
        pass
    
if __name__ == '__main__':
    main()
