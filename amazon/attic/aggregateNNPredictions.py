#!/usr/local/bin/python

"""
Aggregates NN predictions to report on average square error.
"""

from optparse import OptionParser
import csv
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <csvfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputFileName = args[0]
    if not os.path.isfile(inputFileName):
        print >> sys.stderr, 'Cannot find input file: %s' % inputFileName
        return

    with open(inputFileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        count = 0
        totalError = 0
        totalSquareError = 0
        totalZeroError = 0
        totalZeroSquareError = 0
        for row in reader:
            count += 1
            score = float(row[2])
            prediction = float(row[3])
            error = prediction - score
            totalError += error
            totalSquareError += error**2
            totalZeroError += score
            totalZeroSquareError += score**2
    avgError = totalError/count
    avgSquareError = totalSquareError/count
    avgZeroError = totalZeroError/count
    avgZeroSquareError = totalZeroSquareError/count
    print '                    count = %d' % count
    print '               mean error = %0.4f' % avgError
    print '       mean squared error = %0.4f' % avgSquareError
    print '        mean "zero" error = %0.4f' % avgZeroError
    print 'mean "zero" squared error = %0.4f' % avgZeroSquareError

if __name__ == '__main__':
    main()
