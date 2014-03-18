#!/usr/local/bin/python

"""
Generate histogram data for prediction errors aggregated by user via
aggregatePredictions.py.
"""

from optparse import OptionParser
import csv
import os
import sys

# params
userIdIdx = 0
countIdx = 1
averageIdx = 2
varianceIdx = 3
absAverageIdx = 4
uncertaintyIdx = 5

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-b', '--bins', type='int', dest='numBins', default=100,
        help='Number of bins.', metavar='NUM')
    return parser

def incrementBin(bins, error):
    bins[int(round((error)*(len(bins) - 1)/2.0))] += 1

def makeHistogram(reader, bins):
    for row in reader:
        absAverage = float(row[absAverageIdx])
        incrementBin(bins, absAverage)
    return bins

def printHistogram(writer, bins):
    for i in range(len(bins)):
        writer.writerow([round((i + 0.5)*2.0/len(bins), 3), bins[i]])

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

    # Open input file
    print >> sys.stderr, 'Reading from %s . . .' % inputFileName
    inputfile = open(inputFileName, 'r')
    reader = csv.reader(inputfile)

    # Generate histogram data
    bins = [0]*options.numBins
    bins = makeHistogram(reader, bins)

    # Print histogram data
    writer = csv.writer(sys.stdout)
    printHistogram(writer, bins)

if __name__ == '__main__':
    main()
