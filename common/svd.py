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
    parser.add_option('-s', '--savefile', dest='savefile',
        default='data/svd.npz',
        help='Save file for SVD matrix factors and singular values.',
        metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] matrix.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    matrixfname = args[0]
    if not os.path.isfile(matrixfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % matrixfname
        return

    # load matrix
    print 'Loading matrix from %s. . .' % matrixfname
    npzfile = np.load(matrixfname)
    matrix = npzfile['matrix']
    dictionary = npzfile['dictionary']

    # do svd
    print 'Performing SVD. . .'
    u, s, v = np.linalg.svd(matrix)

    ## write SVD products to disk
    print 'Saving SVD products to %s. . .' % options.savefile
    np.savez(options.savefile, u=u, s=s, v=v, dictionary=dictionary)

if __name__ == '__main__':
    main()
