#!/usr/local/bin/python

from optparse import OptionParser
import sqlite3
import os
import sys
import math
import numpy

# params
targetProductId = 'B000002H2H'
K = 20
sigma = 1.1

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
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc', default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1"'),
        metavar='FUNCNAME')
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

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    try:
        cosineFunc = globals()[options.cosineFunc]
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return
    global K
    if options.K:
        K = options.K
    global sigma
    if options.sigma:
        sigma = options.sigma

    print 'targetProductId = %s' % targetProductId

    # connect to db
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)
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
    totalError = 0
    totalSquaredError = 0
    db_curs.execute(selectTargetsStmt, (targetProductId,))
    while True:
        row = db_curs.fetchone()
        if not row:
            break
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
                #print 'No proxy review.'
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

        # make prediction and print error
        if weights:
            count += 1
            total = 0
            for i in range(len(weights)):
                total += weights[i]*scores[i]
            prediction = total/sum(weights)
            error = float(prediction) - float(targetScore)
            squaredError = error**2
            totalError += error
            totalSquaredError += squaredError
            print '-------------------------'
            print '    UserId: %s' % targetUserId
            print 'True Score: %0.3f' % targetScore
            print 'Prediction: %0.3f' % prediction
            print '     Error: %0.3f' % error
            print '   Error^2: %0.3f' % squaredError
            sys.stdout.flush()

    # Print stats
    avgError = totalError/count
    avgSquaredError = totalSquaredError/count
    print '    count = %d' % count
    print '  <error> = %0.3f' % avgError
    print '<error^2> = %0.3f' % avgSquaredError
    
if __name__ == '__main__':
    main()
