#!/usr/local/bin/python

from optparse import OptionParser
import os
import sys
import math
import numpy as np
from scipy.optimize import brentq

"""
Determine a estimate for item-item similarity given two product ratings by
a single reviewer.
"""

# "official" modelSim params
#mu_s = 0.27 # topEdges_80_randSim
mu_s = 0.16 # topEdges_40_randSim
#mu_s = 0.050 # topEdges_80_prefSim
sigma_s = 0.3 # randSim
#sigma_s = 0.050 # prefSim
#mu_r = 0.085 # topEdges_80
mu_r = 0.25 # fix
#mu_r = 0.026 # topEdges_40
sigma_r = 0.3 # randSim
#sigma_r = 0.15 # prefSim

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
    return parser

def modelSim(rating1, rating2):
    p = (rating1 - mu_r)*(rating2 - mu_r)
    q = (rating1 - mu_r)**2 + (rating2 - mu_r)**2
    extremum = brentq(lambda s: -p*s**2 + q*s - p +\
                  (sigma_r/sigma_s)**2*(1 - s**2)**2*(s - mu_s) +\
                  -sigma_r**2*(1 - s**2)*s,
                  -100, 100, xtol=0.0001)
    if extremum > 1:
        return 1
    elif extremum < -1:
        return -1
    else:
        return extremum

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
    
    print modelSim(rating1, rating2)
                          
if __name__ == '__main__':
    main()
