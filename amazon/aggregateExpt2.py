#!/usr/local/bin/python

"""
Aggregates results of experiment 2 into a single data file.
"""

from optparse import OptionParser
import sqlite3
import csv
import os
import sys
from fnmatch import fnmatch

import similarity

# params
outputFileTemplate = '%s.csv'
numUsersIdx = 0
numUsers1Idx = 1
numUsers2Idx = 2
numUsersComIdx = 3
simIdx = 4

# db params
dbTimeout = 5
selectReviewsStmt =\
    ('SELECT Time, UserId, AdjustedScore '
     'FROM Reviews '
     'WHERE ProductId = :ProductId '
     'ORDER BY UserId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-c', '--cosineFunc', dest='cosineFunc',
        default='randSim',
        help=('Similarity function to use for estimate of truth: '
             '"prefSim" or "randSim" (default)'), metavar='FUNCNAME')
    parser.add_option('-p', '--pattern', dest='pattern', default='*.csv',
        help='Input file pattern.', metavar='PATTERN')
    return parser

def getNumCommonUsers(csvFileName):
    f = open(csvFileName, 'rb')
    reader = csv.reader(f)
    return [int(row[numUsersComIdx]) for row in reader]

def getData(csvFileName):
    f = open(csvFileName, 'rb')
    reader = csv.reader(f)
    return [row for row in reader]

def getLastRow(csvFileName):
    with open(csvFileName, 'rb') as f:
        reader = csv.reader(f)
        lastRow = reader.next()
        for row in reader:
            lastRow = row
        return lastRow

def getVariances(csvFileName, truth):
    f = open(csvFileName, 'rb')
    reader = csv.reader(f)
    return [(float(row[simIdx]) - truth)**2 for row in reader]

def getErrors(csvFileName, truth):
    f = open(csvFileName, 'rb')
    reader = csv.reader(f)
    return [float(row[simIdx]) - truth for row in reader]

def main():
    # Parse options
    usage = 'Usage: %prog [options] <inputDir>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputDir = args[0]
    if not os.path.isdir(inputDir):
        print >> sys.stderr, 'Cannot find: %s' % inputDir
        return
    try:
        cosineFunc = getattr(similarity, options.cosineFunc)
    except KeyError:
        print >> sys.stderr,\
            'Invalid Similarity function: %s' % options.cosineFunc
        return

    # connect to db
    db_conn = sqlite3.connect(options.db_fname, dbTimeout)
    db_curs = db_conn.cursor()

    # Compute variances and errors
    data = []
    variances = []
    errors = []
    filenames = []
    for filename in os.listdir(inputDir):
        fullpath = os.path.join(inputDir, filename)
        if not os.path.isfile(fullpath):
            continue
        if not fnmatch(filename, options.pattern):
            continue
        print >> sys.stderr, 'Processing %s . . .' % filename
        filenames.append(filename)
        # record all data
        data.append(getData(fullpath))
        # parse productIds from filename
        productId1 = filename.split('_')[1]
        productId2 = filename.split('_')[2].split('.')[0]
        # fetch product reviews
        db_curs.execute(selectReviewsStmt, (productId1,))
        reviews1 = [row for row in db_curs.fetchall()]
        db_curs.execute(selectReviewsStmt, (productId2,))
        reviews2 = [row for row in db_curs.fetchall()]
        #Deterine best estimate of truth ("gold standard")
        truth, numUserCommon = cosineFunc(reviews1, reviews2)
        # Compute and save variances for this file
        variances.append(getVariances(fullpath, truth))
        # Compute and save errors for this file
        errors.append(getErrors(fullpath, truth))

    assert(len(variances) > 0)

    # Aggregate results
    avgVariance = []
    avgError = []
    avgNumUsers = []
    avgLess = []
    maxVariance = []
    maxFilenames = []
    varVariance = []
    varError = []
    varNumUsers = []
    varLess = []
    finished = False
    j = 0
    while True:
        # Compute averages
        totalVar = 0
        totalErr = 0
        totalNumUsers = 0
        totalLess = 0
        maxVar = 0
        maxFilename = None
        for i in range(len(variances)):
            if j < len(variances[i]):
                if variances[i][j] > maxVar:
                    maxVar = variances[i][j]
                    maxFilename = filenames[i]
                totalVar += variances[i][j]
                totalErr += errors[i][j]
                totalNumUsers += int(data[i][j][numUsersIdx])
                if data[i][j][numUsers1Idx] < data[i][j][numUsers2Idx]:
                    totalLess += int(data[i][j][numUsers1Idx])
                else:
                    totalLess += int(data[i][j][numUsers2Idx])
            else:
                finished = True
                break
        if finished:
            break
        maxVariance.append(maxVar)
        maxFilenames.append(maxFilename)
        avgVariance.append(totalVar/len(variances))
        avgError.append(totalErr/len(errors))
        avgNumUsers.append(totalNumUsers/len(data))
        avgLess.append(totalLess/len(data))
        # Compute variance of variance
        totalVar = 0
        for i in range(len(variances)):
            totalVar += (variances[i][j] - avgVariance[-1])**2
        varVariance.append(totalVar/len(variances))
        # Compute variance of error
        totalErr = 0
        for i in range(len(errors)):
            totalErr += (errors[i][j] - avgError[-1])**2
        varError.append(totalErr/len(errors))
        # Compute variance of num users
        totalNumUsers = 0
        for i in range(len(data)):
            totalNumUsers +=\
                (int(data[i][j][numUsersIdx]) - avgNumUsers[-1])**2
        varNumUsers.append(totalNumUsers/len(data))
        # Compute variance of less reviews
        totalLess = 0
        for i in range(len(data)):
            if data[i][j][numUsers1Idx] < data[i][j][numUsers2Idx]:
                totalLess += (int(data[i][j][numUsers1Idx]) - avgLess[-1])**2
            else:
                totalLess += (int(data[i][j][numUsers2Idx]) - avgLess[-1])**2
        varLess.append(totalLess/len(data))
        j += 1

    # Write results:
    writer = csv.writer(sys.stdout, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    for i in range(len(avgVariance)):
        writer.writerow([i+1,
                         avgVariance[i], varVariance[i],
                         avgError[i], varError[i],
                         avgNumUsers[i], varNumUsers[i],
                         avgLess[i], varLess[i],
                         maxVariance[i], maxFilenames[i]])

if __name__ == '__main__':
    main()
