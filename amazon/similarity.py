#!/usr/local/bin/python

import math
import numpy
import csv
import sys

# params
K = 20
sigma = 1.0
writer = csv.writer(sys.stdout)
step = sys.maxint

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

def cosineSim(reviewsA, reviewsB, onlyCommon=False, fudgeFactor=None):
    # compute product biases:
    if reviewsA:
        biasA = numpy.mean([review[2] for review in reviewsA])
    else:
        biasA = 0.0
    if reviewsB:
        biasB = numpy.mean([review[2] for review in reviewsB])
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
                varA += scoreA**2
            i += 1
        elif userIdA > userIdB:
            if not onlyCommon:
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

