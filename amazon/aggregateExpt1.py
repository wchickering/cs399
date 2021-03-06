#!/usr/local/bin/python

"""
Aggregates results of experiment 1 into a single data file.
"""

from optparse import OptionParser
import csv
import os
import sys
from fnmatch import fnmatch

# params
outputFileTemplate = '%s.csv'
numUsersIdx = 0
numUsers1Idx = 1
numUsers2Idx = 2
numUsersComIdx = 3
simIdx = 4

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-p', '--pattern', dest='pattern', default='*.csv',
        help='Input file pattern.', metavar='PATTERN')
    return parser

def getNumUsers(csvFileName):
    f = open(csvFileName, 'rb')
    reader = csv.reader(f)
    return [int(row[numUsersIdx]) for row in reader]

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

    # Compute variances and errors
    numUsers = []
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
        # record NumUsers for first file only (useful later)
        if not variances:
            numUsers = getNumUsers(fullpath)
        # record all data
        data.append(getData(fullpath))
        # Determine estimate of truth
        lastRow = getLastRow(fullpath)
        truth = float(lastRow[simIdx])
        # Compute and save variances for this file
        variances.append(getVariances(fullpath, truth))
        # Compute and save errors for this file
        errors.append(getErrors(fullpath, truth))

    assert(len(variances) > 0)

    # Aggregate results
    avgVariance = []
    avgError = []
    avgCommonUsers = []
    avgLess = []
    maxVariance = []
    maxFilenames = []
    varVariance = []
    varError = []
    varCommonUsers = []
    varLess = []
    finished = False
    j = 0
    while True:
        # Compute averages
        totalVar = 0
        totalErr = 0
        totalCommonUsers = 0
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
                totalCommonUsers += int(data[i][j][numUsersComIdx])
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
        avgCommonUsers.append(totalCommonUsers/len(data))
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
        # Compute variance of common users
        totalCommonUsers = 0
        for i in range(len(data)):
            totalCommonUsers +=\
                (int(data[i][j][numUsersComIdx]) - avgCommonUsers[-1])**2
        varCommonUsers.append(totalCommonUsers/len(data))
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
        writer.writerow([numUsers[i],
                         avgVariance[i], varVariance[i],
                         avgError[i], varError[i],
                         avgCommonUsers[i], varCommonUsers[i],
                         avgLess[i], varLess[i],
                         maxVariance[i], maxFilenames[i]])

if __name__ == '__main__':
    main()
