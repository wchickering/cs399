#!/usr/local/bin/python

from optparse import OptionParser
import os
import sys
import random
import math

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-r', '--randomSeed', type='int', dest='randomSeed',
        default=0, help='Seed for random module.', metavar='NUM')
    parser.add_option('-d', '--dimensions', type='int', dest='dimensions',
        default=100, help='Number of dimensions.', metavar='NUM')
    parser.add_option('-s', '--sigma', type='float', dest='sigma',
        default=1.0, help='Standard deviation of guassian distribution.',
        metavar='FLOAT')
    return parser

def cosineSimSim(dimensions, sigma, mu1, mu2):
    innerProd = 0
    var1 = 0
    var2 = 0
    count = 0
    for i in range(dimensions):
        elem1 = random.gauss(mu1, sigma)
        elem2 = random.gauss(mu2, sigma)
        innerProd += elem1*elem2
        var1 += elem1**2
        var2 += elem2**2
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

    # Run simulation
    simsim = cosineSimSim(options.dimensions, options.sigma, rating1, rating2)

    # Output
    print simsim
                          
if __name__ == '__main__':
    main()
