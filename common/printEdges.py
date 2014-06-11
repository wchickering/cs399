#!/usr/bin/env python

"""
Prints the degrees of each node
"""

from optparse import OptionParser
import os
import sys
import pickle
import math

#local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] edges.pickle popDict.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # load edges and popularity dictionaries
    edges_fname = getAndCheckFilename(args[0])
    popDict_fname = getAndCheckFilename(args[1])
    edges = loadPickle(edges_fname)
    popDict = loadPickle(popDict_fname)

    # build pop dictionary
    print 'Node1\tNode2\tPop1\tPop2'
    count1 = 0
    count2 = 0
    for node1, node2 in edges:
        if node1 not in popDict:
            count1 += 1
            continue
        if node2 not in popDict:
            count2 += 1
            continue
        pop1 = popDict[node1]
        pop2 = popDict[node2]
        print '%d\t%d\t%d\t%d' % (node1, node2, pop1, pop2)
    print count1
    print count2

if __name__ == '__main__':
    main()
