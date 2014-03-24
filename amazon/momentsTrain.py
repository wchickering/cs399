#!/usr/local/bin/python

"""
Use method of moments to learn mu, sigma1 and sigma2_n for each n.
Take as input the output of regressionTrainData.py and produce parameters file
for use by momSim.
"""

from optparse import OptionParser
import csv
import os
import sys
import mlpy

# params
scoreIdx = 0
trueScoreIdx = 1

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--max-common-reviewers', dest='maxUsersCommon',
        type='int', default=100, help='Maximum number of common reviewers.',
        metavar='NUM')
    return parser

def mean(scores):
    total = 0.0
    for score in scores:
        total += float(score)
    return total / len(scores)

def variance(scores):
    total = 0.0
    sqrTotal = 0.0
    for score in scores:
        score = float(score)
        total += score
        sqrTotal += score*score
    mean = total / len(scores)
    secondMoment = sqrTotal / len(scores)
    return secondMoment - mean*mean

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

    # setup output writer
    writer = csv.writer(sys.stdout)

    # process data
    inputfileTemplate = '%d.csv'
    for numUsersCommon in range(1, options.maxUsersCommon+1):
        inputfileName = inputfileTemplate % numUsersCommon
        #print 'Processing %s . . .' % inputfileName
        fullpath = os.path.join(inputDir, inputfileName)
        if not os.path.isfile(fullpath):
            print >> sys.stderr, 'ERROR: Cannot find %s' % fullpath
            break
        with open(fullpath, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            # read data
            data = [row for row in reader]
            scores = [row[scoreIdx] for row in data]
            trueScores = [row[trueScoreIdx] for row in data]
            # first two rows of output are mu and sigma1
            if numUsersCommon == 1:
                writer.writerow(['mu', mean(trueScores)])
                writer.writerow(['sigma1', variance(trueScores)])
            # write sigma2s
            writer.writerow([numUsersCommon, variance(scores)])

if __name__ == '__main__':
    main()
