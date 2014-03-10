#!/usr/local/bin/python

"""
Computes the similarity between products as a function of the number of common
reviewers, K.
"""

from optparse import OptionParser
import sqlite3
import math
import random
import os
import csv

# params
trainFileTemplate = 'Train_%s_in_common.csv'
testFileName = 'Testset.csv'

# db params
selectGlobalBiasStmt = 'SELECT Value FROM Globals WHERE Key = "Bias"'
selectReviewsStmt =\
    ('SELECT R.UserId, R.Score - PB.Bias - UB.Bias '
     'FROM Reviews AS R, ProductBiases AS PB, UserBiases AS UB '
     'WHERE R.ProductId = PB.ProductId '
     'AND R.UserId = UB.UserId '
     'AND R.ProductId = :ProductId '
     'ORDER BY R.UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--train-dir', dest='trainDir', default='train',
        help='Output directory for training set.', metavar='DIR')
    parser.add_option('--test-dir', dest='testDir', default='test',
        help='Output directory for testing set.', metavar='DIR')
    parser.add_option('-s', '--step', dest='step', type='int', default=1,
        help='Step size for K.', metavar='NUM')
    return parser


def main():
    # Parse options
    usage = 'Usage: %prog [options] inputDir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputdirname = args[0]
    if not os.path.isdir(inputdirname):
        print >> sys.stderr, 'Cannot find: %s' % inputdirname
        return

    print 'Reading files in %s. . .' % inputdirname
    for root, _, files in os.walk(inputdirname):
        for filename in files:
            rand = random.random()
            with open(os.path.join(inputdirname, filename), 'r') as f:
                # Get last line
                for line in f:
                    pass
                line = line.replace('\r', '');
                line = line.replace('\n', '');
                lastScore = line.split(',')[-1]
                f.seek(0)
                for line in f:
                    line = line.replace('\r', "");
                    line = line.replace('\n', '');
                    tokens = line.split(',')
                    num_in_common = tokens[0]
                    tokens.append(lastScore)
                    # Sample - approximately 70% to training, 30% to test
                    if rand < .7:
                        # Don't worry about large number in common cases
                        if int(num_in_common) > 100:
                            break
                        # Write each line to proper file, with last appended
                        trainFileName = os.path.join(options.trainDir, trainFileTemplate % (num_in_common))
                        with open(trainFileName, 'ab') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(tokens)
                    else:
                        testFileFullName = os.path.join(options.testDir, testFileName)
                        with open(testFileFullName, 'ab') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(tokens)
            
if __name__ == '__main__':
    main()
