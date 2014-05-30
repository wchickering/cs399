#!/usr/bin/env python
"""
Helper functions for prediction and evaluation scripts
"""

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
