#!/usr/local/bin/python

"""
Computes the similarity between products as a function of the number of common
reviewers, K.
"""

from optparse import OptionParser
import sqlite3
import math
import os
import csv

# params
outputFileTemplate = '%s_%s.csv'

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
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default='output',
        help='Output directory.', metavar='DIR')
    parser.add_option('-s', '--step', dest='step', type='int', default=10,
        help='Step size for K.', metavar='NUM')
    return parser

def calcAndWriteSims(scoresA, scoresB, step, writer):
    count = 0
    innerProd = 0
    varA = 0
    varB = 0
    i = 0
    j = 0
    while i < len(scoresA) and j < len(scoresB):
        if scoresA[i][0] < scoresB[j][0]:
            varA += scoresA[i][1]**2
            i += 1
        elif scoresA[i][0] > scoresB[j][0]:
            varB += scoresB[j][1]**2
            j += 1
        else:
            count += 1
            innerProd += scoresA[i][1]*scoresB[j][1]
            varA += scoresA[i][1]**2
            varB += scoresB[j][1]**2
            i += 1
            j += 1
            if count % step == 0:
                if innerProd == 0:
                    cosineSim = 0
                else:
                    cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
                writer.writerow([count, cosineSim])

def main():
    # Parse options
    usage = 'Usage: %prog [options] <csvfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # Retrieve the global bias
        db_curs.execute(selectGlobalBiasStmt)
        globalBias = float(db_curs.fetchone()[0])
        print 'Global Bias = %.3f' % globalBias

        with open(inputfilename, 'r') as inputfile:
            for line in inputfile:
                tokens = line.split(',')
                productId1 = tokens[0].strip()
                productId2 = tokens[1].strip()
                outputFileName = os.path.join(options.outputDir,
                                              outputFileTemplate %
                                              (productId1, productId2))
                print 'Writing %s . . .' % outputFileName
                with open(outputFileName, 'wb') as csvfile:
                    writer = csv.writer(csvfile)
                    db_curs.execute(selectReviewsStmt, (productId1,))
                    scores1 = [(row[0], row[1] - globalBias)\
                               for row in db_curs.fetchall()]
                    db_curs.execute(selectReviewsStmt, (productId2,))
                    scores2 = [(row[0], row[1] - globalBias)\
                               for row in db_curs.fetchall()]
                    calcAndWriteSims(scores1, scores2, options.step, writer)

if __name__ == '__main__':
    main()
