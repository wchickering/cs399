#!/usr/local/bin/python

"""
Evaluates the linear regression predictor
"""

from optparse import OptionParser
import sqlite3
import math
import random
import os
import csv
import numpy as np
import mlpy

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-p', '--paramsFile', dest='paramsFile',
            default='regressionParams.csv', help='File with regression' +
            ' parameters', metavar='FILE')
    parser.add_option('-o', '--outputFile', dest='outputFile', default='regResults.csv', 
            help='File to output results of evaluation', metavar='FILE')
    return parser

def predict(params, n, x):
    if not n in params:
        return x
    b = float(params[n][1])
    m = float(params[n][2])
    return m*x + b

def addToDict(dictionary, index, val):
    if not index in dictionary:
        dictionary[index] = val
    dictionary[index] += val

def avgDict(total_dict, time):
    avg_dict = {}
    for num_in_common in time:
        avg_dict[num_in_common] = total_dict[num_in_common]/time[num_in_common]
    return avg_dict

def writeTimeDicts(err, abs_err, sqr_err, reg_err, reg_abs_err, reg_sqr_err, outfile):
    with open(outfile, 'wb') as out:
        writer = csv.writer(out)
        # header
        header = [];
        header.append("num_in_common")
        header.append("avg_error")
        header.append("avg_abs_error")
        header.append("avg_sqr_error")
        header.append("reg_avg_error")
        header.append("reg_avg_abs_error")
        header.append("reg_avg_sqr_error")
        writer.writerow(header)
        for num_in_common in err:
            output = [];
            output.append(num_in_common)
            output.append(err[num_in_common])
            output.append(abs_err[num_in_common])
            output.append(sqr_err[num_in_common])
            output.append(reg_err[num_in_common])
            output.append(reg_abs_err[num_in_common])
            output.append(reg_sqr_err[num_in_common])
            writer.writerow(output)

def main():
    # Parse options
    usage = 'Usage: %prog [options] testFile'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    testFile = args[0]
    if not os.path.isfile(testFile):
        print >> sys.stderr, 'Cannot find: %s' % testFile
        return
    
    params = {}
    with open(options.paramsFile, 'r') as f:
        for line in f:
            tokens=line.split(',')
            params[int(tokens[0])] = tokens

    with open(testFile, 'r') as f:
        total_error = 0
        total_abs_error = 0
        total_sqr_error = 0
        total_error_time = {}
        total_abs_error_time = {}
        total_sqr_error_time = {}
        total_regression_error = 0
        total_regression_abs_error = 0
        total_regression_sqr_error = 0
        total_regression_error_time = {}
        total_regression_abs_error_time = {}
        total_regression_sqr_error_time = {}
        num_lines = 0
        time = {}
        for line in f:
            num_lines += 1
            tokens = line.split(',')
            num_in_common = int(tokens[0])
            addToDict(time, num_in_common, 1)
            score = float(tokens[1])
            predicted_score = predict(params, num_in_common, score)
            final_score = float(tokens[2])
            # calculate errors
            error = (score - final_score)
            total_error += error
            total_abs_error += abs(error)
            total_sqr_error += error*error
            addToDict(total_error_time, num_in_common, error)
            addToDict(total_abs_error_time, num_in_common, abs(error))
            addToDict(total_sqr_error_time, num_in_common, error*error)
            # calculate errors for regression
            regression_error = (predicted_score - final_score)
            total_regression_error += regression_error
            total_regression_abs_error += abs(regression_error)
            total_regression_sqr_error += regression_error*regression_error
            addToDict(total_regression_error_time, num_in_common, regression_error)
            addToDict(total_regression_abs_error_time, num_in_common,
                    abs(regression_error))
            addToDict(total_regression_sqr_error_time, num_in_common,
                    regression_error*regression_error)
        # average it out
        avg_error = total_error/num_lines
        avg_abs_error = total_abs_error/num_lines
        avg_sqr_error = total_sqr_error/num_lines
        avg_regression_error = total_regression_error/num_lines
        avg_regression_abs_error = total_regression_abs_error/num_lines
        avg_regression_sqr_error = total_regression_sqr_error/num_lines
        # averages over time
        avg_error_time = avgDict(total_error_time, time)
        avg_abs_error_time = avgDict(total_abs_error_time, time)
        avg_sqr_error_time = avgDict(total_sqr_error_time, time)
        avg_regression_error_time = avgDict(total_regression_error_time, time)
        avg_regression_abs_error_time = avgDict(total_regression_abs_error_time, time)
        avg_regression_sqr_error_time = avgDict(total_regression_sqr_error_time, time)
        writeTimeDicts(avg_error_time, avg_abs_error_time, avg_sqr_error_time,
                avg_regression_error_time, avg_regression_abs_error_time,
                avg_regression_sqr_error_time, options.outputFile)

        print '========== BASELINE =========='
        print 'Average error = ' + str(avg_error)
        print 'Average absolute error = ' + str(avg_abs_error)
        print 'Average square error = ' + str(avg_sqr_error)
        print
        print '========== REGRESSION =========='
        print 'Average error = ' + str(avg_regression_error)
        print 'Average absolute error = ' + str(avg_regression_abs_error)
        print 'Average absolute error = ' + str(avg_regression_sqr_error)
        print
            
if __name__ == '__main__':
    main()
