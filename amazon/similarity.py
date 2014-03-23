#!/usr/local/bin/python

"""
Module containing various similarity estimating functions that take two lists of
review relations, one for each product in a pair.
"""

import math
import numpy as np
import csv
import sys
from collections import defaultdict
import sympy 

import predictions as pred
from SimilarityGrid import SimilarityGrid

# params
constSimScore = 0.27
K = 20
sigma = 1.0
writer = csv.writer(sys.stdout)
step = sys.maxint

# modelSim params
mu_s = constSimScore
sigma_s = 0.2
sigma_r = 0.3

# errorFile
userIdIdx = 0
averageIdx = 2
varianceIdx = 3
absAverageIdx = 4

def regSim(reviewsA, reviewsB):
    """Uses params from linear regressions on training data to translate
       raw similarity to an improved esimate.
    """
    rawSim, numUsersCommon = regSim_rawFunc(reviewsA, reviewsB)
    if numUsersCommon <= regSim_maxCommonUsers:
        intercept, slope = regSimParams[numUsersCommon]
        return (intercept + slope*rawSim, numUsersCommon)
    else:
        return (rawSim, numUsersCommon)

def constSim(reviewsA, reviewsB):
    """Provides a baseline similarity function by always returning the
       average item-item similarity.
    """
    return (constSimScore, countUsersCommon(reviewsA, reviewsB))

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
       items A and B based on historic rating and similarity scores.
    """
    # compute product biases:
    if reviewsA:
        biasA = np.mean([review[2] for review in reviewsA])
    else:
        biasA = 0.0
    if reviewsB:
        biasB = np.mean([review[2] for review in reviewsB])
    else:
        biasB = 0.0
    totalScore = 0
    totalCount = 0
    numUsersCommon = 0
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
            entry = simGrid[(scoreA, scoreB)]
            if entry:
                totalScore += entry[0]
                totalCount += entry[1]
            i += 1
            j += 1
    if totalCount > 0:
        return (totalScore/totalCount, numUsersCommon)
    else:
        return (constSimScore, numUsersCommon)

def modelSim(reviewsA, reviewsB):
    """this is just a place holder."""
    raise NotImplemented

def weightedModelSim(reviewsA, reviewsB):
    """this is just a place holder."""
    raise NotImplemented

def printPredictions(predictions, weights):
    for p in predictions:
        print 'W: %0.3f, R1: % 0.3f, R2: % 0.3f, P: % 0.3f' %\
            (weights[p[0]], p[1], p[2], p[3])

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

def countUsersCommon(reviewsA, reviewsB):
    numUsersCommon = 0
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
            i += 1
            j += 1
    return numUsersCommon

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
avgWeight = None

def computePredictivity(absAverage, variance, epsilon):
    adjustedError = absAverage 
    return math.exp(-adjustedError/epsilon)

def initWeightedSim(errorFileName, epsilon):
    global weights
    global avgWeight
    w = {}
    totalW = 0
    with open(errorFileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            userId = row[userIdIdx]
            absAverage = float(row[absAverageIdx])
            variance = float(row[varianceIdx])
            w[userId] = computePredictivity(absAverage, variance, epsilon)
            totalW += w[userId]
    # create entry for unknown users
    averageW = totalW/len(w)
    avgWeight = averageW
    weights = defaultdict(lambda x: averageW, w)

#########################
#
#  Linear Regression
#
##############################

regSimParams = {}
regSim_rawFunc = None
regSim_maxCommonUsers = 0

numUsersCommonIdx = 0
interceptIdx = 1
slopeIdx = 2

def initRegSim(paramFileName, cosineFunc, maxCommonUsers):
    global regSimParams
    global regSim_rawFunc
    global regSim_maxCommonUsers
    regSim_rawFunc = cosineFunc
    regSim_maxCommonUsers = maxCommonUsers
    with open(paramFileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            numUsersCommon = int(row[numUsersCommonIdx])
            intercept = float(row[interceptIdx])
            slope = float(row[slopeIdx])
            regSimParams[numUsersCommon] = (intercept, slope)

#################
#
#  predSim
#
####################

simGrid = None

def initPredSim(minRating, maxRating, stepRating, simGridFileName):
    global simGrid
    simGrid = SimilarityGrid(minRating, maxRating, stepRating)
    simGridFile = open(simGridFileName, 'rb')
    simGrid.readFromFile(simGridFile)

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
    parser.add_option('--regSimRawFunc', dest='regSimRawFunc',
        default='randSim',
        help=('Similarity function to used for raw similarity by regSim: '
              '"prefSim", or "randSim" (default)'), metavar='FUNCNAME')
    parser.add_option('--regSimParamsFile', dest='regSimParamsFile',
        default='output/regSim_params.csv', help='Parameter file for regSim.',
        metavar='FILE')
    parser.add_option('--max-common-reviewers', dest='maxUsersCommon',
        type='int', default=100,
        help='Maximum number of common reviewers for regSim.', metavar='NUM')
    parser.add_option('--simGridFile', dest='simGridFile',
        default='output/simGrid_randSim.csv',
        help='CSV containing simGrid data for predSim.', metavar='FILE')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-2.0, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=2.0, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.1, help='Step rating.', metavar='FLOAT')
    parser.add_option('-K', dest='K', type='int', default=None,
        help='Parameter K for prefSimAlt1 or randSimAlt1.', metavar='NUM')
    parser.add_option('--sigma', dest='sigma', type='float', default=None,
        help='Parameter sigma for prefSimAlt1 or randSimAlt1.', metavar='FLOAT')
    parser.add_option('--errorFileName', dest='errorFileName',
        default='output/aggregatePredictions_modelSim.csv',
        help='User prediction errors file for weightedModelSim.', metavar='FILE')
    parser.add_option('--epsilon', dest='epsilon', type='float', default=0.01,
        help='Decay constant epsilon for weightedPredSim.', metavar='FLOAT')
    return parser

def main():
    global K
    global sigma

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
    try:
        regSimRawFunc = globals()[options.regSimRawFunc]
    except KeyError:
        print >> sys.stderr,\
            'Invalid Raw Similarity function: %s' % options.regSimRawFunc
        return

    # set global params
    K = options.K
    sigma = options.sigma

    if options.cosineFunc == 'regSim':
        # retrieve linear regression params
        initRegSim(options.regSimParamsFile, regSimRawFunc,
                   options.maxUsersCommon)

    if options.cosineFunc == 'predSim':
        # read simGrid
        initPredSim(options.minRating, options.maxRating, options.stepRating,
                    options.simGridFile)

    if options.cosineFunc == 'weightedModelSim':
        # initialize weights
        initWeightedSim(options.errorFileName, options.epsilon)

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

