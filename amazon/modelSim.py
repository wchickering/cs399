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
sigma_s = 0.3
mu_r = 0.2
sigma_r = 0.2
alpha = 2

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--mu_s', type='float', dest='mu_s', default=None,
        help='Mean of score distribution.', metavar='FLOAT')
    parser.add_option('--sigma_s', type='float', dest='sigma_s', default=None,
        help='Standard deviation of score distribution.', metavar='FLOAT')
    parser.add_option('--mu_r', type='float', dest='mu_r', default=None,
        help='Mean of rating distribution.', metavar='FLOAT')
    parser.add_option('--sigma_r', type='float', dest='sigma_r', default=None,
        help='Standard deviation of rating distribution.', metavar='FLOAT')
    parser.add_option('--alpha', type='int', dest='alpha', default=None,
        help='Similarity root.', metavar='INT')
    return parser

def modelSim(rating1, rating2):
    # rounding seems to help sympy
    p = round((rating1 - mu_r)*(rating2 - mu_r), 3)
    q = round((rating1 - mu_r)**2 + (rating2 - mu_r)**2, 3)
    mu_s_ = round(mu_s, 3)
    sigRatio = round(alpha*(sigma_r/sigma_s)**2, 3)
    exp1 = round((1 + alpha)/float(alpha), 3)
    exp2 = round((1 - alpha)/float(alpha), 3)
    exp3 = round((3 - alpha)/float(alpha), 3)
    exp4 = round(2/alpha, 3)
    s = Symbol('s')
    solutions = None
    try:
        solutions = solve(q*s - p*s**exp1 - p*s**exp2 + p*s**exp3 +\
                          sigRatio*(1 - s**exp4)**2*(s - mu_s_), s)
    except:
        print >> sys.stderr, 'WARNING: sympy.solve raised error.'
    prediction = None
    if not solutions:
        prediction = mu_s
    else:
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
                print >> sys.stderr,\
                    ('p=%0.3f, q=%0.3f, mu_s_=%0.3f, sigRatio=%0.3f, '
                     'exp1=%0.3f, exp2=%0.3f, exp3=%0.3f, exp4=%0.3f ') %\
                    (p, q, mu_s_, sigRatio, exp1, exp2, exp3, exp4)
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
    global mu_r
    if options.mu_r:
        mu_r = options.mu_r
    global sigma_r
    if options.sigma_r:
        sigma_r = options.sigma_r
    global alpha
    if options.alpha:
        alpha = options.alpha
    
    print modelSim(rating1, rating2)
                          
if __name__ == '__main__':
    main()
