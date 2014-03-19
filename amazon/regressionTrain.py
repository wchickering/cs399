#!/usr/local/bin/python

"""
Perform linear regressions on similarity scores.
Take as input the output of regressionTrainData.py and produce parameters file
for use by regSim.
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

def linearRegression(x, y):
    x2d = []
    for i in x:
        x2d.append([i, 0])
    ols = mlpy.OLS()
    ols.learn(x2d, y)
    params = []
    params.append(ols.beta0())
    params.append(ols.beta()[0])
    return params

def getSqrError(params, x, y):
    totalSqrError = 0
    b = params[0]
    m = params[1]
    for i in range(len(x)):
        prediction = m*float(x[i]) + b
        totalSqrError += (prediction - float(y[i]))*(prediction - float(y[i]))
    return totalSqrError

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
            # do linear regression
            params = linearRegression(scores, trueScores)
            sqrError = getSqrError(params, scores, trueScores)
            # write params
            writer.writerow([numUsersCommon] + params + [len(data), sqrError])

if __name__ == '__main__':
    main()
