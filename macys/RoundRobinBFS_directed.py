#!/usr/local/bin/python

"""
Performs a breadth first search (BFS) originating from multiple sources. Returns
the first K nodes visited.
"""

from collections import deque

def roundRobinBFS(graph, sources, ignores, k):

    # create circular queue of queues
    # and initialize each queue
    queues = deque(maxlen=len(sources))
    for s in sources:
        q = deque()
        for neighbor in graph[s][0]:
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
        for neighbor in graph[n][0]:
            if neighbor not in visited:
                q.appendleft(neighbor)
        if q:
            queues.appendleft(q)
    return found


##########################
# ROUGH UNIT TEST
##########################

import pickle

# params
graph_fname = 'data/recDirectedGraph.pickle'

def loadGraph():
    with open(graph_fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    graph = loadGraph()
    sources = set([45, 74])
    ignores = set([888757, 826391])
    k = 10
    found = roundRobinBFS(graph, sources, ignores, k)
    print 'found =', found

if __name__ == '__main__':
    main()
