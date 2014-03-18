#!/usr/local/bin/python

from optparse import OptionParser
import os
import sys
import random
import math
import numpy as np

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-r', '--randomSeed', type='int', dest='randomSeed',
        default=0, help='Seed for random module.', metavar='NUM')
    parser.add_option('-d', '--dimensions', type='int', dest='dimensions',
        default=10000, help='Number of dimensions.', metavar='NUM')
    parser.add_option('--sigmaXX', type='float', dest='sigmaXX', default=1.0,
       help=('Diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    parser.add_option('--sigmaXY', type='float', dest='sigmaXY', default=0.3,
       help=('Off-diagonal component of covariance matrix for multivariate '
             'Gaussian distribution prior for ratings.'), metavar='FLOAT')
    return parser

def cosineSimSim(dimensions, mu, sigma):
    assert(sigma.shape == (2, 2))
    assert(mu.shape == (2,))
    innerProd = 0
    var1 = 0
    var2 = 0
    count = 0
    for i in range(dimensions):
        elements = np.random.multivariate_normal(mu, sigma)
        innerProd += elements[0]*elements[1]
        var1 += elements[0]**2
        var2 += elements[1]**2
    return innerProd/(math.sqrt(var1)*math.sqrt(var2))

def main():
    # Parse options
    usage = 'Usage: %prog [options] rating1 rating2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    rating1 = float(args[0])
    rating2 = float(args[1])
    

    # Seed random module
    random.seed(options.randomSeed)

    # Form mu vector and sigma matrix
    mu = np.array([rating1, rating2])
    sigma = np.array([[options.sigmaXX, options.sigmaXY],
                      [options.sigmaXY, options.sigmaXX]])

    # Run simulation
    simsim = cosineSimSim(options.dimensions, mu, sigma)

    # Output
    print simsim
                          
if __name__ == '__main__':
    main()
