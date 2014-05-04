#!/usr/bin/env python

"""
Performs singular value decomposition on a matrix.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', dest='k', type='int', default=10,
        help='Rank of computed latent space.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile', default='svd.npz',
        help='Save file for SVD products.', metavar='FILE')
    return parser

def loadMatrices(args):
    matrix = None
    dictionary = None
    for i in range(len(args)):
        filename = args[i]
        if not os.path.isfile(filename):
            print >> sys.stderr, 'ERROR: Cannot find %s' % filename
            return
        print 'Loading matrix from %s. . .' % filename
        npzfile = np.load(filename)
        m = npzfile['matrix']
        d = npzfile['dictionary']
        if matrix is None:
            matrix = m
            dictionary = d
        else:
            if m.shape[1] != matrix.shape[1]:
                print >> sys.stderr,\
                    'ERROR: All matrices must have same number of columns.'
                return
            if not equalLists(d, dictionary):
                print >> sys.stderr,\
                    'ERROR: All matrix dictionaries must be equal.'
                return
            numRows = matrix.shape[0] + m.shape[0]
            numCols = matrix.shape[1]
            matrix = np.append(matrix, m).reshape([numRows, numCols])
    return matrix, dictionary

def equalLists(listA, listB):
    if len(listA) != len(listB):
        return False
    for i in range(len(listA)):
        if listA[i] != listB[i]:
            return False
    return True

def main():
    # Parse options
    usage = 'Usage: %prog [options] matrix1.npz matrix2.npz matrix3.npz ...'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error('ERROR: Must provide at least one matrix file.')

    # load matrices
    matrix, dictionary = loadMatrices(args)

    # do svd
    print 'Performing SVD. . .'
    u, s, v = np.linalg.svd(matrix, full_matrices=False)

    # write SVD products to disk
    print 'Saving SVD products to %s. . .' % options.savefile
    k = options.k
    assert(k > 0 and k <= u.shape[1])
    np.savez(options.savefile, u=u[:,0:k], s=s[0:k], v=v[0:k,:],
             dictionary=dictionary)

if __name__ == '__main__':
    main()
