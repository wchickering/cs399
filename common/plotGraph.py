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

# params
saveFormat = 'jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Treat as a directed graph.')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def stronglyConnectedComponents(graph):
    """
    Finds strongly connected components of a directed graph.
    
    Code written by Mark Dickinson (MIT) and posted to:
    http://code.activestate.com/recipes/578507-strongly-connected-components-of-a-directed-graph/
    on 4/2/2013
    
    Notes
        -----
		The algorithm has running time proportional to the total number of
        vertices and edges.  It's practical to use this algorithm on graphs with
        hundreds of thousands of vertices and edges.
    
		The algorithm is recursive.  Deep graphs may cause Python to exceed its
        recursion limit.
    
		The nodes of `graph` will be iterated over exactly once, and edges of
        `graph[v]` will be iterated over exactly once for each vertex `v`.
        `graph[v]` is permitted to specify the same vertex multiple times, and
        it's permissible for `graph[v]` to include `v` itself.  (In
        graph-theoretic terms, loops and multiple edges are permitted.)
    
		References
        ----------
        .. [1] Harold N. Gabow, "Path-based depth-first search for strong and
           biconnected components," Inf. Process. Lett. 74 (2000) 107--114.
    
		.. [2] Robert E. Tarjan, "Depth-first search and linear graph
           algorithms," SIAM J.Comput. 1 (2) (1972) 146--160.
    """
    identified = set()
    stack = []
    index = {}
    boundaries = []

    def dfs(v):
        index[v] = len(stack)
        stack.append(v)
        boundaries.append(index[v])

        for w in graph[v][0]:
            if w not in index:
                for scc in dfs(w):
                    yield scc
            elif w not in identified:
                while index[w] < boundaries[-1]:
                    boundaries.pop()

        if boundaries[-1] == index[v]:
            boundaries.pop()
            scc = set(stack[index[v]:])
            del stack[index[v]:]
            identified.update(scc)
            yield scc

    for v in graph:
        if v not in index:
            for scc in dfs(v):
                yield scc

def plotSCCHist(graph, numBins, savedir, show=False):
    components = [c for c in stronglyConnectedComponents(graph)]
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

def components(graph):
    comps = {}
    c = 0
    for source in graph:
        if source in comps:
            continue
        q = deque()
        q.appendleft((source, 0))
        while q:
            (n, x) = q.pop()
            if n in comps: continue
            comps[n] = c
            for neighbor in graph[n][0]:
                if neighbor in comps: continue
                q.appendleft((neighbor, x+1))
        c += 1
    return comps

def componentSizes(graph):
    comps = components(graph)
    sizes = defaultdict(int)
    for node in comps:
        sizes[comps[node]] += 1
    return sizes

def plotCompHist(graph, numBins, savedir, show=False):
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
    if show:
        plt.show()

def plotInDegreeDist(graph, numBins, savedir, show=False):
    data = []
    for node in graph:
        data.append(len(graph[node][1]))
    n, bins, patches = plt.hist(data, bins=numBins, range=(0, numBins-1))
    plt.title('In-Degree Distribution')
    plt.ylabel('Number of Nodes')
    plt.xlabel('In-Degree')
    savefile = os.path.join(savedir, 'indegree.%s' % saveFormat)
    print 'Saving In-Degree Distribution to %s. . .' % savefile
    plt.savefig(savefile)
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
        print >> sys.stderr, 'ERROR: Cannot find %s' % graphfname
        return
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
            print >> sys.stderr, 'ERROR: Cannot find dir: %s' % options.savedir
            return

    # load graph
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    if options.directed:
        # strongly connected components histogram
        print 'Plotting SCC histogram. . .'
        plotSCCHist(graph, options.bins, options.savedir, show=options.show)
    else:
        # components histogram
        print 'Plotting Components histogram. . .'
        plotCompHist(graph, options.bins, options.savedir, show=options.show)

    # in-degree distribution
    print 'Plotting in-degree distribution. . .'
    plotInDegreeDist(graph, options.bins, options.savedir, show=options.show)

if __name__ == '__main__':
    main()
