#!/usr/bin/env python

"""
Finds components of the recommendation graph, labeling each item with its
component number.
"""

import pickle
from collections import deque

# params
graph_fname = 'recGraph.pickle'
components_fname = 'recComponents.pickle'

def loadGraph():
    with open(graph_fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def findComponents(graph):
    components = {}
    q = deque()
    c = 0
    for node in graph:
        if node in components:
            continue
        cnt = 0
        c_list = []
        c += 1
        print 'Traversing component %d' % c
        q.appendleft(node)
        while q:
            n = q.pop()
            if n in components:
                continue
            components[n] = c
            cnt += 1
            c_list.append(n)
            for child in graph[n]:
                q.appendleft(child)
        print '    found %d nodes' % cnt
        if cnt < 10:
            print c_list
    return components

def main():
    graph = loadGraph()
    components = findComponents(graph)
    pickle.dump(components, open(components_fname, 'w'))

if __name__ == '__main__':
    main()
