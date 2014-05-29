#!/usr/bin/env python

import numpy as np
import math

"""
Helper functions for use with Latent Semantic Indexing  via
rank-reduced numpy.linalg.svd() products.
"""

def loadLSIModel(npzfile):
    u = npzfile['u']
    s = npzfile['s']
    v = npzfile['v']
    nodes = npzfile['dictionary']
    dictionary = {}
    for i in range(len(nodes)):
        dictionary[i] = int(nodes[i])
    # data returned: each row is a product, each column is a topic
    data = u
    return data, dictionary

def getTermConcepts(u, s):
    # matrix returned: rows are topics, columns are products
    return np.transpose(u) # Don't weight topics differently
    #return np.transpose(u.dot(np.diag(s))) # Weight by topic importance

def showConcept(u, concept, topn=10, reverse=True, dictionary=None):
    termValues = u[:,concept]
    return sorted([((value, str(dictionary[term]))\
                    if dictionary is not None else (value, term))\
                   for term, value in enumerate(termValues)],
                  key=lambda x: x[0], reverse=reverse)[0:topn]

def conceptCorrelation(u, conceptA, conceptB):
    meanA = sum(u[:,conceptA])/u.shape[0]
    meanB = sum(u[:,conceptB])/u.shape[0]
    numerator = np.dot(u[:,conceptA] - meanA, u[:,conceptB] - meanB)
    varianceA = np.dot(u[:,conceptA] - meanA, u[:,conceptA] - meanA)
    varianceB = np.dot(u[:,conceptB] - meanA, u[:,conceptB] - meanB)
    return numerator/math.sqrt(varianceA*varianceB)

