#!/usr/bin/env python

"""
Produce a variety of plots for the purpose of analyzing a graph.
"""

from optparse import OptionParser
import matplotlib.pyplot as plt
import pickle
import os
import sys
from collections import deque
from collections import defaultdict

# local modules
from Graph_util import loadGraph, getComponents, getSCCs

# params
saveFormat = 'jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Treat as a directed graph.')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save plots in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def plotSCCHist(graph, savedir, numBins=100, show=False):
    components = [c for c in getSCCs(graph)]
    sizes = [len(c) for c in components]
    data = []
    for s in sizes:
        data += [s]*s
    n, bins, patches = plt.hist(data, bins=numBins)
    plt.title('Strongly Connected Components')
    plt.ylabel('Number of Nodes')
    plt.xlabel('Component Size')
    savefile = os.path.join(savedir, 'scchist.%s' % saveFormat)
    print 'Saving SCC Histogram to %s. . .' % savefile
    plt.savefig(savefile)
    if show:
        plt.show()

def componentSizes(graph):
    comps = getComponents(graph)
    sizes = defaultdict(int)
    for node in comps:
        sizes[comps[node]] += 1
    return sizes

def plotCompHist(graph, savedir, numBins=100, show=False):
    sizes = componentSizes(graph)
    data = []
    for c in sizes:
        data += [sizes[c]]*sizes[c]
    n, bins, patches = plt.hist(data, bins=numBins)
    plt.title('Components')
    plt.ylabel('Number of Nodes')
    plt.xlabel('Component Size')
    savefile = os.path.join(savedir, 'comphist.%s' % saveFormat)
    print 'Saving Component Histogram to %s. . .' % savefile
    plt.savefig(savefile)
    plt.figure()
    if show:
        plt.show()

def plotInDegreeDist(graph, savedir, numBins=30, show=False):
    data = []
    for node in graph:
        data.append(len(graph[node][1]))
    n, bins, patches = plt.hist(data, bins=numBins, range=(0, numBins))
    plt.title('In-Degree Distribution')
    plt.ylabel('Number of Nodes')
    plt.xlabel('In-Degree')
    savefile = os.path.join(savedir, 'indegree.%s' % saveFormat)
    print 'Saving In-Degree Distribution to %s. . .' % savefile
    plt.savefig(savefile)
    plt.figure()
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        parser.error('Cannot find %s' % graphfname)
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

    # load graph
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    if options.directed:
        # strongly connected components histogram
        print 'Plotting SCC histogram. . .'
        plotSCCHist(graph, options.savedir, numBins=options.bins,
                    show=options.show)
    else:
        # components histogram
        print 'Plotting Components histogram. . .'
        plotCompHist(graph, options.savedir, numBins=options.bins,
                     show=options.show)

    # in-degree distribution
    print 'Plotting in-degree distribution. . .'
    plotInDegreeDist(graph, options.savedir, show=options.show)

if __name__ == '__main__':
    main()
