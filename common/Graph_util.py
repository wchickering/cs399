#!/usr/bin/env python

"""
Helper functions for working with graphs.
"""

from collections import deque
import pickle

class GraphError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def saveGraph(graph, fname):
    pickle.dump(graph, open(fname, 'w'))

def extractNodes(graph, nodes):
    for node in nodes:
        if node not in graph:
            continue
        for neighbor in graph[node][0]:
            graph[neighbor][1].remove(node)
        for neighbor in graph[node][1]:
            graph[neighbor][0].remove(node)
        del graph[node]

def addNodes(graph, nodes):
    for node in nodes:
        if node in graph:
            raise GraphError('Node %d already exists' % node)
        graph[node] = ([], [])

def addEdges(graph, edges):
    for edge in edges:
        if edge[0] not in graph:
            raise GraphError('Node %d not in graph' % edge[0])
        if edge[1] not in graph:
            raise GraphError('Node %d not in graph' % edge[1])
        graph[edge[0]][0].append(edge[1])
        graph[edge[1]][1].append(edge[0])

def mergeGraphs(graph1, graph2):
    """Assumes graph1 and graph2 are disjoint."""
    graph = {}
    for g in [graph1, graph2]:
        addNodes(graph, g.keys())
        for node in g:
            graph[node][0].extend(g[node][0])
            graph[node][1].extend(g[node][1])
    return graph

def getComponents(graph):
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

def getComponentLists(graph):
    components = getComponents(graph)
    lists = [[None] for i in range(max(components.values())+1)]
    for node, comp in components.items():
        lists[comp].append(node)
    return lists

def getSCCs(graph):
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
