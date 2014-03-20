#!/usr/local/bin/python

from optparse import OptionParser
import os
import sys
import math
import numpy as np
from sympy import Symbol, Eq, solve
from sympy.solvers.solvers import check_assumptions

"""
Determine a estimate for item-item similarity given two product ratings by
a single reviewer.
"""

# "official" modelSim params
mu_s = 0.27
sigma_s = 0.2
sigma_r = 0.2

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--mu_s', type='float', dest='mu_s',
        default=None, help='Mean of score distribution.',
        metavar='FLOAT')
    parser.add_option('--sigma_s', type='float', dest='sigma_s',
        default=None, help='Standard deviation of score distribution.',
        metavar='FLOAT')
    parser.add_option('--sigma_r', type='float', dest='sigma_r',
        default=None, help='Standard deviation of rating distribution.',
        metavar='FLOAT')
    return parser

def modelSim(rating1, rating2):
    # rounding seems to help sympy
    mu = round(mu_s, 3)
    sigRatio = round((sigma_r/sigma_s)**2, 3)
    p = round(rating1*rating2, 3)
    q = round(rating1**2 + rating2**2, 3)
    s = Symbol('s')
    try:
        solutions = solve(-p*s**2 + q*s - p +\
                          sigRatio*(1 - s**2)**2*(s - mu), s)
    except:
        print >> sys.stderr, 'WARNING: sympy.solve raised error.'
        solutions = []
    prediction = None
    for candidate in solutions:
        if (check_assumptions(candidate, real=True) and\
            candidate > -1 and candidate < 1) or\
             candidate == 0:
            prediction = candidate
    if not prediction:
        if solutions == [0.0]:
            prediction = 0.0
        elif solutions and solutions[0] == 1.0:
            prediction = 1.0
        elif solutions and solutions[0] == -1.0:
            prediction = -1.0
        else:
            print >> sys.stderr, 'WARNING: No solution found:', solutions
            prediction = mu_s
    return prediction

def main():
    # Parse options
    usage = 'Usage: %prog [options] rating1 rating2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    rating1 = float(args[0])
    rating2 = float(args[1])
    global mu_s
    if options.mu_s:
        mu_s = options.mu_s
    global sigma_s
    if options.sigma_s:
        sigma_s = options.sigma_s
    global sigma_r
    if options.sigma_r:
        sigma_r = options.sigma_r
    
    print modelSim(rating1, rating2)
                          
if __name__ == '__main__':
    main()
