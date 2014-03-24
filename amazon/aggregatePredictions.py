#!/usr/local/bin/python

"""
Aggregates results of predictions.py into a single data file.
"""

from optparse import OptionParser
import csv
import os
import sys
import math
from fnmatch import fnmatch

# params
userIdIdx = 0
rating1Idx = 1
rating2Idx = 2
predictionIdx = 3
errorIdx = 4

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-p', '--pattern', dest='pattern', default='*.csv',
        help='Input file pattern.', metavar='PATTERN')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <inputDir>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputDir = args[0]
    if not os.path.isdir(inputDir):
        print >> sys.stderr, 'Cannot find: %s' % inputDir
        return

    # compile user predictions
    userErrors = {}
    for filename in os.listdir(inputDir):
        fullpath = os.path.join(inputDir, filename)
        if not os.path.isfile(fullpath):
            continue
        if not fnmatch(filename, options.pattern):
            continue
        print >> sys.stderr, 'Processing %s . . .' % filename
        with open(fullpath, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                userId = row[userIdIdx]
                #rating1 = float(row[rating1Idx])
                #rating2 = float(row[rating2Idx])
                #prediction = float(row[predictionIdx])
                error = float(row[errorIdx])
                if userId in userErrors:
                    userErrors[userId].append(error)
                else:
                    userErrors[userId] = [error]

    # compute average error and square error
    # and write output
    grandTotalCount = 0
    grandTotalAbsError = 0
    grandTotalSquareError = 0
    writer = csv.writer(sys.stdout)
    for userId in userErrors:
        total = 0
        squareTotal = 0
        absTotal = 0
        count = len(userErrors[userId])
        for error in userErrors[userId]:
            total += error
            squareTotal += error**2
            absTotal += abs(error)
            grandTotalCount += 1
            grandTotalAbsError += abs(error)
            grandTotalSquareError += error**2
        average = total/count
        if count > 1:
            variance = squareTotal/(count - 1)
            uncertainty = math.sqrt(variance/count)
        else:
            variance = float('inf')
            uncertainty = float('inf')
        absAverage = absTotal/count
        writer.writerow([userId, count, average, variance, absAverage,
                         uncertainty])
    grandAverageAbsError = grandTotalAbsError/grandTotalCount
    grandErrorVariance = grandTotalSquareError/(grandTotalCount - 1)
    print >> sys.stderr,\
        'grandAverageAbsError = %0.3f, grandErrorVariance = %0.3f' %\
        (grandAverageAbsError, grandErrorVariance)

if __name__ == '__main__':
    main()
