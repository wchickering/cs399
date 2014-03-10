#!/usr/local/bin/python

"""
Computes parameters of linear regression for each training file output by
reegressionTrainTest.py.
"""

from optparse import OptionParser
import sqlite3
import math
import random
import os
import csv
import numpy as np
import mlpy

# params
trainFileTemplate = 'Train_%s_in_common.csv'
testFileName = 'Testset.csv'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--outputFile', dest='outFile',
            default='regressionParams.csv', help='Output file for regression' +
            ' parameters', metavar='FILE')
    parser.add_option('-s', '--step', dest='step', type='int', default=1,
        help='Step size for K.', metavar='NUM')
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
    usage = 'Usage: %prog [options] trainDir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    trainDir = args[0]
    if not os.path.isdir(trainDir):
        print >> sys.stderr, 'Cannot find: %s' % trainDir
        return

    print 'Reading files in %s. . .' % trainDir
    for root, _, files in os.walk(trainDir):
        for filename in files:
            with open(os.path.join(trainDir, filename), 'r') as f:
                scores = []
                final_scores = []
                num_points = 0
                for line in f:
                    tokens = line.split(',')
                    num_in_common = tokens[0]
                    scores.append(tokens[1])
                    final_scores.append(tokens[2])
                    num_points += 1
                params = linearRegression(scores, final_scores)
                # Construct output for csv: (num_in_common, b, m, num_points, sqr_error)
                output = []
                output.append(num_in_common)
                output += params
                output.append(num_points)
                output.append(getSqrError(params, scores, final_scores))
                with open(options.outFile, 'ab') as out:
                    writer = csv.writer(out)
                    writer.writerow(output)
            
if __name__ == '__main__':
    main()
