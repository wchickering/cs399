#!/usr/bin/env python

"""
Compares the probability distributions over a graph, presumably resulting from
random walks, contained in the rows of two equal-sized, square matrices.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
import math

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--nodiag', action='store_true', dest='nodiag',
        default=False, help='Zero out matrix diagonals before comparison.')
    return parser

def cosineSim(vecA, vecB):
    numerator = np.dot(vecA, vecB)
    denominator = math.sqrt(np.dot(vecA, vecA)*np.dot(vecB, vecB))
    if denominator == 0.0:
        return float('nan')
    else:
        return numerator/denominator

def translateMatrix(sMatrix, sDictionary, tDictionary):
    tNode2id = {}
    for i in range(len(tDictionary)):
        tNode2id[tDictionary[i]] = i
    transMatrix = np.array(sMatrix)
    for index, item in sDictionary.items():
        # swap columns
        transMatrix[:,[index,tNode2id[item]]] =\
            transMatrix[:,[tNode2id[item],index]]
        # swap rows
        transMatrix[[index,tNode2id[item]],:] =\
            transMatrix[[tNode2id[item],index],:]
    return transMatrix


def compareMatrices(sMatrix, tMatrix):
    #sNorm = np.sqrt(np.diag(np.dot(sMatrix.T, sMatrix)))
    #tNorm = np.sqrt(np.diag(np.dot(tMatrix.T, tMatrix)))
    #norm = sNorm * tNorm
    #return sum(np.diag(np.dot(sMatrix.T, tMatrix)) / norm)/sMatrix.shape[0]
    simTotal = 0.0
    simCnt = 0
    for i in range(sMatrix.shape[0]):
        sim = cosineSim(sMatrix[i,:], tMatrix[i,:])
        if not math.isnan(sim):
            simTotal += cosineSim(sMatrix[i,:], tMatrix[i,:])
            simCnt += 1
    return simTotal/simCnt

def main():
    # Parse options
    usage = 'Usage: %prog [options] targetMatrix.npz sourceMatrix.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments.')
    sFilename = args[0]
    if not os.path.isfile(sFilename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % sFilename
        return
    tFilename = args[1]
    if not os.path.isfile(tFilename):
        print >> sys.stderr, 'ERROR: Cannot find %s' % tFilename
        return

    # load matrices
    print 'Loading matrix from %s. . .' % sFilename
    npzfile = np.load(sFilename)
    sMatrix = npzfile['matrix']
    d = npzfile['dictionary']
    sDictionary = {}
    for i in range(len(d)):
        sDictionary[i] = int(d[i])
    print 'Loading matrix from %s. . .' % tFilename
    npzfile = np.load(tFilename)
    tMatrix = npzfile['matrix']
    d = npzfile['dictionary']
    tDictionary = {}
    for i in range(len(d)):
        tDictionary[i] = int(d[i])
    if sMatrix.shape[0] != sMatrix.shape[1] or\
       tMatrix.shape[0] != tMatrix.shape[1]:
        print >> sys.stderr, 'ERROR: Matrices must be square.'
        return
    if sMatrix.shape[0] != tMatrix.shape[0]:
        print >> sys.stderr, 'ERROR: Matrices must be of equal rank.'
        return

    if options.nodiag:
        ## check for off-diagonal probability mass
        #epsilon = 0.000001
        #cnt = 0
        #for i in range(sMatrix.shape[0]):
        #    if abs(1.0 - sMatrix[i,i]) < epsilon:
        #        cnt += 1
        #if cnt > 0:
        #    print >> sys.stderr,\
        #        'WARNING: %d rows of sMatrix with 1.0 on diagonal' % cnt
        #cnt = 0
        #for i in range(tMatrix.shape[0]):
        #    if abs(1.0 - tMatrix[i,i]) < epsilon:
        #        cnt += 1
        #if cnt > 0:
        #    print >> sys.stderr,\
        #        'WARNING: %d rows of tMatrix with 1.0 on diagonal' % cnt

        # zero out the diagonal
        print 'Zeroing out matrix diagonals. . .'
        sMatrix -= np.diag(np.diag(sMatrix))
        tMatrix -= np.diag(np.diag(tMatrix))

    # translate source matrix to target coords
    print 'Translating from source to target coordinates. . .'
    transSMatrix = translateMatrix(sMatrix, sDictionary, tDictionary)

    # compute the average distribution similarity
    print 'Comparing matrices. . .'
    similarity = compareMatrices(transSMatrix, tMatrix)

    # display result
    print 'Similarity: %.3f' % similarity

if __name__ == '__main__':
    main()
