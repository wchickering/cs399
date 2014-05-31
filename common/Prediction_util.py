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

def filterByPopularity(data, dictionary, popDictionary, minPop):
    data_new = None
    dictionary_new = {}
    j = 0
    for i in range(data.shape[0]):
        if popDictionary[dictionary[i]] >= minPop:
            if data_new is None:
                data_new = data[i,:].reshape(1, data.shape[1])
            else:
                data_new = np.concatenate(
                    (data_new, data[i,:].reshape(1, data.shape[1]))
                )
            dictionary_new[j] = dictionary[i]
            j += 1
    return data_new, dictionary_new
