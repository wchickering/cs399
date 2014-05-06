#!/usr/bin/env python

"""
Produce statistics and plots in order to compares two graphs.
"""

from optparse import OptionParser
import matplotlib.pyplot as plt
import pickle
import os
import sys
from collections import deque
from collections import defaultdict

# params
saveFormat = 'jpg'

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
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Compare directed graphs.')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save plots in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    parser.add_option('--distdists', action='store_true', dest='distdists',
        default=False, help='Produce distance distributions.')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def compareGraphs(target, source, directed=False):
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
    if not directed:
       # we double counted in the case of an undirected graph
       comparison.targetEdgeCnt /= 2
       comparison.sourceEdgeCnt /= 2
       comparison.commonEdgeCnt /= 2
       comparison.targetMissEdgeCnt /= 2
       comparison.sourceMissEdgeCnt /= 2
    return comparison

def getDistances(graph, origin, destinations):
    assert(origin in graph)
    assert(len(destinations) > 0)
    for dest in destinations:
       assert(dest in graph)
    goals = set(destinations)
    distances = {}
    q = deque()
    q.appendleft((origin, 0))
    while q:
        (n, x) = q.pop()
        if n in distances: continue
        distances[n] = x
        if n in goals:
            goals.remove(n)
            if len(goals) == 0:
                break
        for neighbor in graph[n][0]:
            if neighbor in distances: continue
            q.appendleft((neighbor, x+1))
    goalDists = {}
    for g in destinations:
        if g in distances:
            goalDists[g] = distances[g]
    return goalDists

def plotDistanceDist(target, source, savedir, title=None, numBins=10,
                     basefile=None, directed=False, show=False):
    nbrDists = defaultdict(int)
    cnt = 0
    for node in target:
        cnt += 1
        distances = getDistances(source, node, target[node][0])
        for neighbor in distances:
            nbrDists[distances[neighbor]] += 1
    data = []
    for dist, cnt in nbrDists.items():
        if directed:
            data += [dist]*cnt
        else:
            data += [dist]*(cnt/2) # adjust for overcounting by 2
    n, bins, patches = plt.hist(data, bins=numBins, range=(0, numBins-1))
    if title is not None:
        plt.title(title)
    plt.ylabel('Number of Neighbors')
    plt.xlabel('Distance')
    if basefile is None:
        basefile = 'distIn'
    savefile = os.path.join(savedir, '%s.%s' % (basefile, saveFormat))
    print 'Saving Distance Distribution to %s. . .' % savefile
    plt.savefig(savefile)
    plt.figure()
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options] <targetGraph.pickle> <sourceGraph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    targetfname = args[0]
    if not os.path.isfile(targetfname):
        parser.error('Cannot find %s' % targetfname)
    sourcefname = args[1]
    if not os.path.isfile(sourcefname):
        parser.error('Cannot find %s' % sourcefname)
    if options.savedir is None:
        savedir = os.getcwd()
    elif os.path.isdir(options.savedir):
        savedir = options.savedir
    else:
        if os.path.isdir(os.path.split(options.savedir)[0]):
            print 'Creating directory %s. . .' % options.savedir
            os.mkdir(options.savedir)
            savedir = options.savedir
        else:
            parser.error('Cannot find dir: %s' % options.savedir)

    # load graphs
    target = loadGraph(targetfname)
    source = loadGraph(sourcefname)

    # compare graphs
    comparison = compareGraphs(target, source, directed=options.directed)

    # display scores
    comparison.display()

    if options.distdists:
        # plot distance distributions
        plotDistanceDist(target, source, options.savedir,
                         title='Distances of Target Neighbors in Source',
                         basefile='distInSrc', directed=options.directed,
                         show=options.show)
        plotDistanceDist(source, target, options.savedir,
                         title='Distances of Source Neighbors in Target',
                         basefile='distInTgt', directed=options.directed,
                         show=options.show)

if __name__ == '__main__':
    main()
