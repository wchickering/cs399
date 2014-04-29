#!/usr/bin/env python

import numpy as np
import math

"""
Helper functions for use with Latent Semantic Indexing  via
rank-reduced numpy.linalg.svd() products.
"""

def getTermConcepts(u, s):
    return np.transpose(u.dot(np.linalg.inv(np.diag(s))))

def showConcept(u, concept, topn=10, reverse=True):
    termValues = u[:,concept]
    return sorted([(value, term) for term, value in enumerate(termValues)],
                  key=lambda x: x[0], reverse=reverse)[0:topn]

def conceptCorrelation(u, conceptA, conceptB):
    meanA = sum(u[:,conceptA])/u.shape[0]
    meanB = sum(u[:,conceptB])/u.shape[0]
    numerator = np.dot(u[:,conceptA] - meanA, u[:,conceptB] - meanB)
    varianceA = np.dot(u[:,conceptA] - meanA, u[:,conceptA] - meanA)
    varianceB = np.dot(u[:,conceptB] - meanA, u[:,conceptB] - meanB)
    return numerator/math.sqrt(varianceA*varianceB)

