#!/usr/bin/env python

"""
Compares two directed graphs.
"""

from optparse import OptionParser
import pickle
import os
import sys

class GraphComparison:
    def __init__(self):
        self.targetNodeCnt = 0
        self.sourceNodeCnt = 0
        self.targetEdgeCnt = 0
        self.sourceEdgeCnt = 0
        self.commonNodeCnt = 0
        self.commonEdgeCnt = 0
        self.targetMissNodeCnt = 0
        self.sourceMissNodeCnt = 0
        self.targetMissEdgeCnt = 0
        self.sourceMissEdgeCnt = 0

    def display(self):
        print 'target node cnt: %d' % self.targetNodeCnt
        print 'source node cnt: %d' % self.sourceNodeCnt
        print 'target edge cnt: %d' % self.targetEdgeCnt
        print 'source edge cnt: %d' % self.sourceEdgeCnt
        print 'nodes in common: %d' % self.commonNodeCnt
        print 'edges in common: %d' % self.commonEdgeCnt
        print 'nodes missing from target: %d' % self.targetMissNodeCnt
        print 'nodes missing from source: %d' % self.sourceMissNodeCnt
        print 'edges missing from target: %d' % self.targetMissEdgeCnt
        print 'edges missing from source: %d' % self.sourceMissEdgeCnt

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def compareGraphs(target, source):
    comparison = GraphComparison()
    for node in target:
        comparison.targetNodeCnt += 1
        comparison.targetEdgeCnt += len(target[node][0])
        if node in source:
            comparison.commonNodeCnt += 1
            for neighbor in target[node][0]:
                if neighbor in source[node][0]:
                    comparison.commonEdgeCnt += 1
                else:
                    comparison.sourceMissEdgeCnt += 1
        else:
            comparison.sourceMissNodeCnt += 1
            comparison.sourceMissEdgeCnt += len(target[node][0])
    for node in source:
        comparison.sourceNodeCnt += 1
        comparison.sourceEdgeCnt += len(source[node][0])
        if node in target:
            for neighbor in source[node][0]:
                if neighbor not in target[node][0]:
                    comparison.targetMissEdgeCnt += 1
        else:
            comparison.targetMissNodeCnt += 1
            comparison.targetMissEdgeCnt += len(source[node][0])
    return comparison

def main():
    # Parse options
    usage = 'Usage: %prog [options] <targetGraph.pickle> <sourceGraph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    targetfname = args[0]
    if not os.path.isfile(targetfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % targetfname
        return
    sourcefname = args[1]
    if not os.path.isfile(sourcefname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % sourcefname
        return

    # load graphs
    target = loadGraph(targetfname)
    source = loadGraph(sourcefname)

    # compare graphs
    comparison = compareGraphs(target, source)

    # display scores
    comparison.display()

if __name__ == '__main__':
    main()
