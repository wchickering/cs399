#!/usr/local/bin/python

"""
Generate modelSim scores as a function of a single product rating
while holding the other product rating held fixed.
"""

from optparse import OptionParser
import numpy as np
import csv
import os
import sys

import modelSim

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
        help='Similarity root.', metavar='FLOAT')
    parser.add_option('--minRating', type='float', dest='minRating',
       default=-1.0, help='Minimum rating value.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
       default=2.0, help='Maximum rating value.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
       default=0.1, help='Step rating value.', metavar='FLOAT')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] rating1'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    rating1 = float(args[0])

    # modelSim param overrides
    if options.mu_s:
        modelSim.mu_s = options.mu_s
    if options.sigma_s:
        modelSim.sigma_s = options.sigma_s
    if options.mu_r:
        modelSim.mu_r = options.mu_r
    if options.sigma_r:
        modelSim.sigma_r = options.sigma_r
    if options.alpha:
        modelSim.alpha = options.alpha

    # Generate curve
    writer = csv.writer(sys.stdout)
    rating2 = options.minRating
    while rating2 < options.maxRating:
        sim = modelSim.modelSim(rating1, rating2)
        writer.writerow([round(rating2, 3), sim])
        rating2 += options.stepRating

if __name__ == '__main__':
    main()
