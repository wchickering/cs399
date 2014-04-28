#!/usr/bin/env python

"""
Finds strongly connected components of a directed graph.

Code written by Mark Dickinson (MIT) and posted to:
http://code.activestate.com/recipes/578507-strongly-connected-components-of-a-directed-graph/
on 4/2/2013

Notes
    -----
    The algorithm has running time proportional to the total number of vertices
    and edges.  It's practical to use this algorithm on graphs with hundreds of
    thousands of vertices and edges.

    The algorithm is recursive.  Deep graphs may cause Python to exceed its
    recursion limit.

    The nodes of `graph` will be iterated over exactly once, and edges of 
    `graph[v]` will be iterated over exactly once for each vertex `v`.
    `graph[v]` is permitted to specify the same vertex multiple times, and it's
    permissible for `graph[v]` to include `v` itself.  (In graph-theoretic
    terms, loops and multiple edges are permitted.)

    References
    ----------
    .. [1] Harold N. Gabow, "Path-based depth-first search for strong and
       biconnected components," Inf. Process. Lett. 74 (2000) 107--114.

    .. [2] Robert E. Tarjan, "Depth-first search and linear graph algorithms,"
       SIAM J.Comput. 1 (2) (1972) 146--160.
"""

from optparse import OptionParser
import pickle
import sys
import os
from collections import defaultdict

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--display', dest='display', action='store_true',
        default=False, help='Print components to console.')
    parser.add_option('--savefile', dest='savefile', default=None,
        help='Pickle save file.', metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def stronglyConnectedComponents(graph):
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

    # load graph
    graph = loadGraph(graphfname)

    # find components
    components = [c for c in stronglyConnectedComponents(graph)]

    # print components
    if options.display:
        for c in components:
            print c

    # compile stats
    sizeCnt = defaultdict(int)
    for c in components:
        sizeCnt[len(c)] += 1
    for cnt, cntCnt in sorted(sizeCnt.items()):
        print '%d SCCs with %d nodes' % (cntCnt, cnt)
    print '%d SCCs in total (%d nodes and %d edges in graph)' %\
        (len(components), len(graph), sum([len(graph[n][0]) for n in graph]))

    # save components
    if options.savefile is not None:
        pickle.dump(components, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
