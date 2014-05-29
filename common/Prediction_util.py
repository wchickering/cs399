#!/usr/bin/env python
"""
Helper functions for prediction and evaluation scripts
"""

# params
topn = 100
basePop = 0.000001
alpha = 500.0
import numpy as np

def getPopDictionary(popgraph):
    popDictionary = {}
    for item in popgraph:
        # set popularity equal to in-degree
        popDictionary[item] = len(popgraph[item][1])
    return popDictionary

def makeEdges(neighbors, dictionary):
    predicted_edges = []
    for index, node in dictionary.items():
        predicted_edges += [(node, int(n)) for n in neighbors[index]]
    return predicted_edges

def getNeighbors(data, k, searchEngine, popDictionary):
    if popDictionary is None:
        distances, neighbors =\
            searchEngine.kneighbors(data, n_neighbors=k)
    else:
        distances, neighbors =\
            searchEngine.kneighborsWeighted(data, popDictionary,
                  topn, alpha, basePop, n_neighbors=k)

    return distances, neighbors
