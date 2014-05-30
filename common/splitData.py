#!/usr/bin/env python

from optparse import OptionParser
import random
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-p', type='float', dest='p', default=0.1,
        help=('Each line of input is written to test_ output with probability '
              'p and written to train_ output with probability 1 - p.'),
        metavar='FLOAT')
    parser.add_option('--seed', type='int', dest='seed', default=0,
        help='Seed for random number generator.', metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] datafile'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfname = args[0]
    if not os.path.isfile(inputfname):
        print >> sys.stderr, 'Cannot find %s' % inputfname
        return
    if options.p < 0 or options.p > 1.0:
        print >> sys.stderr, 'Invalid value for param p: %f', options.p
        return

    # seed rng
    random.seed(options.seed)

    # construct output file names
    dirname, basename = os.path.split(inputfname)
    testfname = os.path.join(dirname, 'test_' + basename)
    trainfname = os.path.join(dirname, 'train_' + basename)

    # open files
    inputfile = open(inputfname, 'r')
    testfile = open(testfname, 'w')
    trainfile = open(trainfname, 'w')

    # split data
    for line in inputfile:
        if random.random() < options.p:
            testfile.write(line)
        else:
            trainfile.write(line)

    # close files
    inputfile.close()
    testfile.close()
    trainfile.close()

if __name__ == '__main__':
    main()
