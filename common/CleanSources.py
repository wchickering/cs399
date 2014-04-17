#!/usr/bin/env python

"""
"Cleans" set of graph traversal sources by removing those who have exclusively
visited neighbors.
"""

from collections import deque

def cleanSources(graph, sources, ignores):
    visited = set(sources).union(set(ignores))
    clean_sources = deque()
    for s in sources:
        for neighbor in graph[s][0]:
            if neighbor not in visited:
                clean_sources.appendleft(s)
                break
    return clean_sources

