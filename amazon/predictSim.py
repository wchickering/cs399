#!/usr/local/bin/python

from optparse import OptionParser
import os
import sys

from SimilarityGrid import SimilarityGrid

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--simGridFile', dest='simGridFile',
        default='output/simGrid_randSim.csv',
        help='CSV containing simGrid data.', metavar='FILE')
    parser.add_option('--minRating', type='float', dest='minRating',
        default=-2.0, help='Minimum rating.', metavar='FLOAT')
    parser.add_option('--maxRating', type='float', dest='maxRating',
        default=2.0, help='Maximum rating.', metavar='FLOAT')
    parser.add_option('--stepRating', type='float', dest='stepRating',
        default=0.1, help='Step rating.', metavar='FLOAT')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] rating1 rating2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    rating1 = float(args[0])
    rating2 = float(args[1])

    # Initialize similarity grid
    simGrid = SimilarityGrid(options.minRating, options.maxRating,
                             options.stepRating)
    inputFile = open(options.simGridFile, 'rb')
    simGrid.readFromFile(inputFile)

    # Get entry
    scoreTotal = simGrid[(rating1, rating2)][0]
    count = simGrid[(rating1, rating2)][1]
    if count > 0:
        estimate = scoreTotal/count
    else:
        estimate = '?'
    print ('(%0.3f/%d) =' % (scoreTotal, count)), estimate
 
if __name__ == '__main__':
    main()
