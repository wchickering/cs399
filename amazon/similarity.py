#!/usr/local/bin/python

import math
import numpy as np
import csv
import sys
from collections import defaultdict

import cosineSimSim
import predictions as pred

# params
K = 20
sigma = 1.0
writer = csv.writer(sys.stdout)
step = sys.maxint
dimensions = 100
sigmaXX = 1.0
sigmaXY = 0.3

# errorFile
userIdIdx = 0
averageIdx = 2
varianceIdx = 3

def prefSim(reviewsA, reviewsB):
    """Compute the "preferential" similarity between items A and B.
       This similarity function is the cosine similarity that includes
       ratings by users who have rated both items as well as those
       by users who have rated only one item.
    """
    return cosineSim(reviewsA, reviewsB)

def prefSimAlt1(reviewsA, reviewsB):
    """Compute the "preferential" similarity between items A and B.
       This similarity function is the cosine similarity that includes
       ratings by users who have rated both items as well as those
       by users who have rated only one item.
       Altered Version 1: If the length of a reviews vector is less than K,
           we add (K - len(reviews))*sigma**2 to its variance as used in the
           cosine similarity function, where K and sigma are global parameters.
    """
    return cosineSim(reviewsA, reviewsB, fudgeFactor='simpFudge')

def randSim(reviewsA, reviewsB):
    """Compute the "random" similarity between items A and B.
       This similarity function is the cosine similarity that only
       includes ratings by users who have rated both items.
    """
    return cosineSim(reviewsA, reviewsB, onlyCommon=True)

def randSimAlt1(reviewsA, reviewsB):
    """Compute the "random" similarity between items A and B.
       This similarity function is the cosine similarity that only
       includes ratings by users who have rated both items.
       Altered Version 1: If the length of a reviews vector is less than K,
           we add (K - len(CommonReviewers))*sigma**2 to its variance as
           used in the cosine similarity function, where K and sigma are
           global parameters.
    """
    return cosineSim(reviewsA, reviewsB, onlyCommon=True,
                     fudgeFactor='simrFudge')

def weightedRandSim(reviewsA, reviewsB):
    """Compute the "weighted", "random" similarity between items A and B.
       Ratings are weighted by the "predictivity" of the associated user.
       This similarity function is the cosine similarity that only
       includes ratings by users who have rated both items. Ratings are
       weighted by the associated user's "predictivity".
    """
    return cosineSim(reviewsA, reviewsB, onlyCommon=True, weights=weights)

def predSim(reviewsA, reviewsB):
    """Compute the average "implicitly" predicted similarity between
       items A and B.
    """
    print 'DBG: EXECUTING predSim()'
    sigma = np.array([[sigmaXX, sigmaXY],
                      [sigmaXY, sigmaXX]])
    predictions = pred.getPredictions(dimensions, sigma, reviewsA, reviewsB)
    avgPrediction = np.mean([p[3] for p in predictions])
    return (avgPrediction, len(predictions))

def cosineSim(reviewsA, reviewsB, onlyCommon=False, fudgeFactor=None,
              weights=None):
    # compute product biases:
    if reviewsA:
        biasA = np.mean([review[2] for review in reviewsA])
    else:
        biasA = 0.0
    if reviewsB:
        biasB = np.mean([review[2] for review in reviewsB])
    else:
        biasB = 0.0
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
            if not onlyCommon:
                scoreA = reviewsA[i][2] - biasA
                if weights:
                    scoreA *= weights[userIdA]
                varA += scoreA**2
            i += 1
        elif userIdA > userIdB:
            if not onlyCommon:
                scoreB = reviewsB[j][2] - biasB
                if weights:
                    scoreB *= weights[userIdB]
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
            if weights:
                scoreA *= weights[userIdA]
                scoreB *= weights[userIdB]
            innerProd += scoreA*scoreB
            varA += scoreA**2
            varB += scoreB**2
            i += 1
            j += 1
            if numUsersCommon % step == 0:
                writer.writerow([numUsersCommon,
                                 computeScore(innerProd, varA, varB)])
    if not onlyCommon:
        while i < len(reviewsA):
            scoreA = reviewsA[i][2] - biasA
            varA += scoreA**2
            i += 1
        while j < len(reviewsB):
            scoreB = reviewsB[j][2] - biasB
            varB += scoreB**2
            j += 1
    # Magical simp fudge factor
    if fudgeFactor == 'simpFudge':
        if len(reviewsA) < K:
            varA += (K - len(reviewsA))*sigma**2
        if len(reviewsB) < K:
            varB += (K - len(reviewsB))*sigma**2
    # Magical simr fudge factor
    elif fudgeFactor == 'simrFudge':
        if numUsersCommon < K:
            varA += (K - numUsersCommon)*sigma**2
            varB += (K - numUsersCommon)*sigma**2
    return (computeScore(innerProd, varA, varB), numUsersCommon)

def computeScore(innerProd, varA, varB):
    if innerProd == 0:
        return 0
    else:
        return innerProd/(math.sqrt(varA)*math.sqrt(varB))

#########################
#
#  Weighted Similarity
#
################################

weights = None

def computePredictivity(average, variance, epsilon):
    adjustedError = abs(average) + math.sqrt(variance)
    return math.exp(-adjustedError/epsilon)

def initWeightedSim(errorFileName, epsilon):
    global weights
    w = {}
    totalW = 0
    with open(errorFileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            userId = row[userIdIdx]
            average = float(row[averageIdx])
            variance = float(row[varianceIdx])
            w[userId] = computePredictivity(average, variance, epsilon)
            totalW += w[userId]
    # create entry for unknown users
    averageW = totalW/len(w)
    weights = defaultdict(lambda x: averageW, w)

############
#
#  Stand-alone similarity
#
#################

from optparse import OptionParser
import sqlite3

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
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              'or "predSim"'), metavar='FUNCNAME')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    parser.add_option('--dimensions', type='int', dest='dimensions',
        default=100, help='Number of dimensions.', metavar='NUM')
    parser.add_option('--sigmaXX', type='float', dest='sigmaXX', default=1.0,
       help=('Diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    parser.add_option('--sigmaXY', type='float', dest='sigmaXY', default=0.3,
       help=('Off-diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    return parser

def main():
    global K
    global sigma
    global dimensions
    global sigmaXX
    global sigmaXY

    # Parse options
    usage = 'Usage: %prog [options] productId1 productId2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    productId1 = args[0]
    productId2 = args[1]
    try:
        cosineFunc = globals()[options.cosineFunc]
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return

    # set global params
    K = options.K
    sigma = options.sigma
    dimensions = options.dimensions
    sigmaXX = options.sigmaXX
    sigmaXY = options.sigmaXY

    # connect to db
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)
    db_curs = db_conn.cursor()

    # fetch product reviews
    db_curs.execute(selectReviewsStmt, (productId1,))
    reviews1 = [row for row in db_curs.fetchall()]
    db_curs.execute(selectReviewsStmt, (productId2,))
    reviews2 = [row for row in db_curs.fetchall()]

    # compute cosine similarity using the provided function.
    cosineSim, numUserCommon = cosineFunc(reviews1, reviews2)

    # print score
    print ('(%s) Sim = %0.3f, numUserCommon = %d, '
           'len(reviews1) = %d, len(reviews2) = %d') %\
        (options.cosineFunc, cosineSim, numUserCommon,
         len(reviews1), len(reviews2))
    
if __name__ == '__main__':
    main()

