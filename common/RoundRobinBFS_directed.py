#!/usr/bin/env python

"""
Performs a breadth first search (BFS) originating from multiple sources. Returns
the first K nodes visited.
"""

from collections import deque
from random import shuffle

def roundRobinBFS(graph, sources, ignores, k):

    # create circular queue of queues
    # and initialize each queue
    queues = deque(maxlen=len(sources))
    for s in sources:
        q = deque()
        neighbors = graph[s][0]
        shuffle(neighbors)
        for neighbor in neighbors:
            q.appendleft(neighbor)
        queues.appendleft(q)
   
    found = [] 
    visited = set(sources).union(set(ignores))
    while queues:
        q = queues.pop()
        while q:
            n = q.pop()
            if n not in visited:
                break
        if n in visited:
            continue
        visited.add(n)
        found.append(n)
        if len(found) >= k:
            break
        neighbors = graph[n][0]
        shuffle(neighbors)
        for neighbor in neighbors:
            if neighbor not in visited:
                q.appendleft(neighbor)
        if q:
            queues.appendleft(q)
    return found


##########################
# ROUGH UNIT TEST
##########################

import pickle

# local modules
from Graph_util import loadGraph

# params
graph_fname = 'data/recDirectedGraph.pickle'

def main():
    graph = loadGraph(graph_fname)
    sources = set([45, 74])
    ignores = set([888757, 826391])
    k = 10
    found = roundRobinBFS(graph, sources, ignores, k)
    print 'found =', found

if __name__ == '__main__':
    main()
