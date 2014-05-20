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

# local modules
from Graph_util import loadGraph

# params
saveFormat = 'jpg'

class GraphComparison:
    def __init__(self):
        self.targetNodeCnt = 0
        self.targetEdgeCnt = 0
        self.commonNodeCnt = 0
        self.commonTargetEdgeCnt = 0
        self.sourceMissNodeCnt = 0
        self.sourceMissEdgeCnt = 0
        self.k = 1

    def display(self, tName, sName):
        print '%s node cnt: %d' % (tName, self.targetNodeCnt)
        print '%s edge cnt: %d' % (tName, self.targetEdgeCnt)
        print 'nodes in common: %d' % self.commonNodeCnt
        print '%s edges within %d in %s graph: %d' % \
            (tName, int(self.k), sName, self.commonTargetEdgeCnt)
        print 'nodes missing from %s: %d' % (sName, self.sourceMissNodeCnt)
        print 'edges missing from %s: %d' % (sName, self.sourceMissEdgeCnt)

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
    parser.add_option('-k', dest='k', default=1, metavar='NUM',
        help='Distance away to consider correct.')
    return parser

def compareGraphs(target, source, k, directed=False):
    comparison = GraphComparison()
    comparison.k = k
    for node in target:
        comparison.targetNodeCnt += 1
        comparison.targetEdgeCnt += len(target[node][0])
        if node in source:
            comparison.commonNodeCnt += 1
            distances = getDistances(source, node, target[node][0])
            for neighbor in distances:
                if distances[neighbor] <= k:
                    comparison.commonTargetEdgeCnt += 1
                else:
                    comparison.sourceMissEdgeCnt += 1
        else:
            comparison.sourceMissNodeCnt += 1
            comparison.sourceMissEdgeCnt += len(target[node][0])
    if not directed:
       # we double counted in the case of an undirected graph
       comparison.targetEdgeCnt /= 2
       comparison.commonTargetEdgeCnt /= 2
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
    usage = 'Usage: %prog [options] <targetGraph.pickle> <sourceGraph.pickle>'
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
    comparison_TtoS = compareGraphs(target, source, int(options.k),
            directed=options.directed)
    comparison_StoT = compareGraphs(source, target, int(options.k),
            directed=options.directed)

    # display scores
    comparison_TtoS.display('target', 'source')
    print '-------------------------'
    comparison_StoT.display('source', 'target')

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
