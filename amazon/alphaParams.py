#!/usr/local/bin/python

"""
Fit sigma2_n to the function alpha / sqrt(n).
Take as input the parameter file output from momemtsTrain.py and produce 
alpha parameters file for use by momSim.
"""

from optparse import OptionParser
import csv
import os
import sys
import mlpy
import math

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def harmonic(limit):
    total = 0.0
    for n in range(1, limit+1):
        total += 1.0 / n
    return total

def learnAlpha(sigma2_n):
    harmonicSum = harmonic(len(sigma2_n))
    total = 0.0
    for i in range(len(sigma2_n)):
        total += float(sigma2_n[i]) / math.sqrt(i + 1)
    return total / harmonicSum

def main():
    # parse options
    usage = 'Usage: %prog momParamFile'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputFileName = args[0]
    if not os.path.isfile(inputFileName):
        print >> sys.stderr, 'Cannot find: %s' % inputDir
        return

    # setup output writer
    writer = csv.writer(sys.stdout)

    variableIdx = 0
    valueIdx = 1
    # process data
    with open(inputFileName, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        # read data
        data = [row for row in reader]
        variables = [row[variableIdx] for row in data]
        values = [row[valueIdx] for row in data]
        # first two rows of input are mu and sigma1
        mu = values[0]
        sigma1 = values[1]
        sigma2_n = values[2:]
        alpha = learnAlpha(sigma2_n)
        # write sigma2s
        writer.writerow([mu, sigma1, alpha])

if __name__ == '__main__':
    main()
