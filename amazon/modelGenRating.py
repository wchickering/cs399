#!/usr/local/bin/python

"""
Generates rating pairs given their cosine similarity according to a simple
model.
"""

from optparse import OptionParser
import os
import sys
import numpy as np

import modelSim

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--numRatings', dest='numRatings', type='int',
        default=10, help='Number of rating pairs to generate.', metavar='NUM')
    parser.add_option('--sigma_s', type='float', dest='sigma_s',
        default=None, help='Standard deviation of score distribution.',
        metavar='FLOAT')
    parser.add_option('--sigma_r', type='float', dest='sigma_r',
        default=None, help='Standard deviation of rating distribution.',
        metavar='FLOAT')
    return parser

def genRatings(sigma_s, sigma_r, score):
    mean = np.array([0, 0])
    cov = sigma_r*np.array([[1.0, score],
                            [score, 1.0]])
    return np.random.multivariate_normal(mean, cov)

def main():
    # Parse options
    usage = 'Usage: %prog [options] similarityScore'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    try:
        score = float(args[0])
    except:
        print >> sys.stderr, 'ERROR: Invalid similarity score.'
        return

    # modelSim param overrides
    if options.sigma_s:
        sigma_s = options.sigma_s
    else:
        sigma_s = modelSim.sigma_s
    if options.sigma_r:
        sigma_r = options.sigma_r
    else:
        sigma_r = modelSim.sigma_r

    # generate ratings
    for i in range(options.numRatings):
        rating1, rating2 = genRatings(sigma_s, sigma_r, score)
        print 'rating1 = % 0.3f, rating2 = % 0.3f' % (rating1, rating2)

if __name__ == '__main__':
    main()
