#!/usr/bin/env python

"""
Compare two LSI models produced by svd.py and indicate whether they are
different.
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
    lsifile1 = getAndCheckFilename(args[0])
    lsifile2 = getAndCheckFilename(args[1])

    # load LSI models
    npzfile1 = np.load(lsifile1)
    u1 = npzfile1['u']
    s1 = npzfile1['s']
    v1 = npzfile1['v']
    dictionary1 = npzfile1['dictionary']
    npzfile2 = np.load(lsifile2)
    u2 = npzfile2['u']
    s2 = npzfile2['s']
    v2 = npzfile2['v']
    dictionary2 = npzfile2['dictionary']

    if not np.array_equal(u1, u2) or\
       not np.array_equal(s1, s2) or\
       not np.array_equal(v1, v2):
        print 'LSI models differ.'
    elif len(dictionary1) != len(dictionary2) or\
         (dictionary1 != dictionary2).any():
        print 'Matrices are equal but dictionaries are not.'

if __name__ == '__main__':
    main()
