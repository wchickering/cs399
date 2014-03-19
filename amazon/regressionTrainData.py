#!/usr/local/bin/python

"""
Takes output files from simVsK.py and generates input files for regression.py.
"""

from optparse import OptionParser
import sqlite3
import csv
import os
import sys

# params
numUsersCommonIdx = 0
scoreIdx = 1

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--output-dir', dest='outputDir',
        default='regressionTrainOutput', help='Output directory.', metavar='DIR')
    parser.add_option('-m', '--max-common-reviewers', dest='maxUsersCommon',
        type='int', default=100, help='Maximum number of common reviewers.',
        metavar='NUM')
    return parser

def getTrueScore(fullpath):
    """Retrieves last score in file."""
    trueScore = None
    with open(fullpath, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            trueScore = row[scoreIdx]
    return trueScore

def main():
    # Parse options
    usage = 'Usage: %prog [options] inputDir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputDir = args[0]
    if not os.path.isdir(inputDir):
        print >> sys.stderr, 'Cannot find: %s' % inputDir
        return

    # Create output writers
    outfileTemplate = '%d.csv'
    writers = [None] # create empty entry in order to index from 1
    for i in range(options.maxUsersCommon):
        outfileName = os.path.join(options.outputDir, outfileTemplate % (i+1))
        outfile = open(outfileName, 'wb')
        writers.append(csv.writer(outfile))

    print 'Reading files in %s . . .' % inputDir
    for filename in os.listdir(inputDir):
        fullpath = os.path.join(inputDir, filename)
        if not os.path.isfile(fullpath):
            continue
        print 'Processing %s . . .' % filename
        trueScore = getTrueScore(fullpath)
        with open(fullpath, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                numUsersCommon = int(row[numUsersCommonIdx])
                if numUsersCommon > options.maxUsersCommon:
                    break
                score = float(row[scoreIdx])
                # write output
                writers[numUsersCommon].writerow([score, trueScore])

if __name__ == '__main__':
    main()

