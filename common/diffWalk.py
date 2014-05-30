#!/usr/bin/env python

"""
Compare two walk matrices produced by buildWalkMatrix.py and indicate whether
they are different.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] walkMatrix1.npz walkMatrix2.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    walkfile1 = getAndCheckFilename(args[0])
    walkfile2 = getAndCheckFilename(args[1])

    # load walk matrices
    npzfile1 = np.load(walkfile1)
    matrix1 = npzfile1['matrix']
    dictionary1 = npzfile1['dictionary']
    npzfile2 = np.load(walkfile2)
    matrix2 = npzfile2['matrix']
    dictionary2 = npzfile2['dictionary']

    if not np.array_equal(matrix1, matrix2):
        print 'Walk matrices differ.'
    elif len(dictionary1) != len(dictionary2) or\
         (dictionary1 != dictionary2).any():
        print 'Matrices are equal but dictionaries are not.'

if __name__ == '__main__':
    main()
