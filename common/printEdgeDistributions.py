#!/usr/bin/env python

"""
Prints the degrees of each node
"""

from optparse import OptionParser
import os
import sys
import pickle
import math
from collections import defaultdict
import operator

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
    print 'Node\tOccurances\tPop'
    nodes = defaultdict(int)
    for node1, node2 in edges:
        nodes[node1] += 1
        nodes[node2] += 1
    for node in nodes.keys():
        if node not in popDict:
            popDict[node] = 0
    for node in popDict:
        if node not in nodes:
            nodes[node] = 0
    sorted_by_pop = sorted(nodes.iteritems(), key=lambda (k, v):
            (popDict[k], k), reverse=True)
    for node, occurances in sorted_by_pop:
        print '%d\t%d\t%f' % (node, occurances, popDict[node])

if __name__ == '__main__':
    main()
