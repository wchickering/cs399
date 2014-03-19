#!/usr/local/bin/python

"""
Partition product pairs into a training set and testing test.
"""

from optparse import OptionParser
import os
import sys
import csv
import random

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--fraction', type='float', dest='fraction',
        default=0.3, help='Fraction of pairs in test set.', metavar='FLOAT')
    parser.add_option('--trainOut', dest='trainOut', default=None,
        help='Training pairs output file.', metavar='FILE')
    parser.add_option('--testOut', dest='testOut', default=None,
        help='Testing pairs output file.', metavar='FILE')
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
    progName = os.path.basename(sys.argv[0]).split('.')[0]
    if options.trainOut:
        trainOut = options.trainOut
    else:
        trainOut = 'data/%s.train.csv' % progName
    if options.testOut:
        testOut = options.testOut
    else:
        testOut = 'data/%s.test.csv' % progName

    # open input file
    print 'Reading from %s. . .' % inputFileName
    inFile = open(inputFileName, 'rb') 
    reader = csv.reader(inFile)

    # open output files
    print 'Writing training data to %s . . .' % trainOut
    trainFile = open(trainOut, 'wb')
    trainWriter = csv.writer(trainFile)
    print 'Writing testing data to %s . . .' % testOut
    testFile = open(testOut, 'wb')
    testWriter = csv.writer(testFile)

    # read and shuffle data
    pairs = [(row[0], row[1]) for row in reader]
    random.shuffle(pairs)

    # write data
    trainCount = 0
    testCount = 0
    for pair in pairs:
       if random.random() >= options.fraction:
           trainCount += 1
           trainWriter.writerow(pair)
       else:
           testCount += 1
           testWriter.writerow(pair)
    print '%d Training data, %d Testing data written' % (trainCount, testCount)

if __name__ == '__main__':
    main()
