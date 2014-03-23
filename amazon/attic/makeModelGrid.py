#!/usr/local/bin/python

"""
Compute the similarity score using a simple mode for rating pairs.
"""

from optparse import OptionParser
import csv
import os
import sys
import sympy

from SimilarityGrid import SimilarityGrid

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--mu_s', type='float', dest='mu_s',
        default=0.27, help='Mean of score distribution prior.', metavar='FLOAT')
    parser.add_option('--sigma_s', type='float', dest='sigma_s',
        default=0.2, help='Standard deviation of score distribution prior.',
        metavar='FLOAT')
    parser.add_option('--sigma_r', type='float', dest='sigma_r',
        default=0.1, help='Standard deviation of rating distribution prior.',
        metavar='FLOAT')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-2.0, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=2.0, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.1, help='Step rating.', metavar='FLOAT')
    return parser

def fillGrid(mu_s, sigma_s, sigma_r, simGrid):
    for (rating1, rating2) in simGrid:
        p = round(rating1*rating2, 3)
        q = round(rating1**2 + rating2**2, 3)
        s = sympy.Symbol('s')
        solutions =\
            sympy.solve(-p*s**2 + q*s - p +\
                        (sigma_r/sigma_s)**2*(1 - s**2)**2*(s - mu_s), s)
        if solutions:
            score = solutions[0]
        else:
            print >> sys.stderr, 'WARNING: No solution to eq found.'
            score = mu_s
        print >> sys.stderr,\
            'rating1 = % 0.3f, rating2 = % 0.3f, score = % 0.3f' %\
            (rating1, rating2, score)
        if simGrid[(rating1, rating2)]:
            simGrid[(rating1, rating2)][0] = score
        
def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # Initialize similarity grid
    simGrid = SimilarityGrid(options.minRating, options.maxRating,
                             options.stepRating)

    # Fill similarity grid
    fillGrid(options.mu_s, options.sigma_s, options.sigma_r, simGrid)

    # Write similarity grid to stdout
    simGrid.writeToFile(sys.stdout)

if __name__ == '__main__':
    main()

