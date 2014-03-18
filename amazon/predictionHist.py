#!/usr/local/bin/python

"""
Generate histogram data for predictions (aka "implied" similarities) produced by
predictions.py.
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
    parser.add_option('-b', '--bins', type='int', dest='numBins', default=100,
        help='Number of bins.', metavar='NUM')
    parser.add_option('-p', '--pattern', dest='pattern', default=None,
        help='Input file pattern.', metavar='PATTERN')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='prefSim',
        help=('Similarity function to use: "prefSim" (default), "randSim", '
              '"prefSimAlt1", or "randSimAlt1".'), metavar='FUNCNAME')
    return parser

def incrementBin(bins, cosineSim):
    bins[int(round((1.0 + cosineSim)*(len(bins) - 1)/2.0))] += 1

def makeHistogram(inputDir, pattern, bins):
    for filename in os.listdir(inputDir):
        fullpath = os.path.join(inputDir, filename)
        if not os.path.isfile(fullpath):
            continue
        if not fnmatch(filename, pattern):
            continue
        print >> sys.stderr, 'Processing %s . . .' % filename
        with open(fullpath, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                #userId = row[userIdIdx]
                #rating1 = float(row[rating1Idx])
                #rating2 = float(row[rating2Idx])
                prediction = float(row[predictionIdx])
                #error = float(row[errorIdx])
                incrementBin(bins, prediction)
    return bins

def printHistogram(writer, bins):
    for i in range(len(bins)):
        writer.writerow([round((i + 0.5)*2.0/len(bins) - 1.0, 3), bins[i]])

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
    if options.pattern:
        pattern = options.pattern
    else:
        pattern = '%s_*_*.csv' % options.cosineFunc

    # Generate histogram data
    bins = [0]*options.numBins
    makeHistogram(inputDir, pattern, bins)

    # Print histogram data
    writer = csv.writer(sys.stdout)
    printHistogram(writer, bins)

if __name__ == '__main__':
    main()
