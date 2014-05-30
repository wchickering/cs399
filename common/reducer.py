#!/usr/bin/env python

"""
Takes a sorted csv file containing two columns: a integer-valued key and a
numeric (possibly floating point) value. Outputs the key along with the count,
average, and variance asssociated with that key.
"""

from optparse import OptionParser
import csv
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--outputFileName', dest='outputFileName',
                      default=None, help='Output filename.', metavar='FILE')
    parser.add_option('-b', '--binSize', dest='binSize', type='int', default=1,
                      help='Bin Size.', metavar='INT')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] csvfile'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputFileName = args[0]
    inputFile = open(inputFileName, 'rb')
    reader = csv.reader(inputFile)
    if not os.path.isfile(inputFileName):
        print >> sys.stderr, 'Cannot find: %s' % inputFileName
        return
    if options.outputFileName:
        outputFile = open(options.outputFileName, 'wb')
    else:
        outputFile = sys.stdout
    writer = csv.writer(outputFile)

    # reduce data
    lastKey = None
    keys = []
    values = []
    count = 0
    for row in reader:
        key = int(row[0])
        value = float(row[1])
        if not lastKey:
            lastKey = key
        elif key - lastKey >= options.binSize:
            avgKey = int(round(float(sum(keys))/count))
            avgValue = float(sum(values))/count
            varValue = sum([(float(v) - avgValue)**2 for v in values])/count
            writer.writerow([avgKey, count, avgValue, varValue])
            keys = []
            values = []
            count = 0
            lastKey = key
        keys.append(key)
        values.append(value)
        count += 1
    # write last record
    avgKey = int(round(float(sum(keys))/count))
    avgValue = float(sum(values))/count
    varValue = sum([(float(v) - avgValue)**2 for v in values])/count
    writer.writerow([avgKey, count, avgValue, varValue])

if __name__ == '__main__':
    main()
