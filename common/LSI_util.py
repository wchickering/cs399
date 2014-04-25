#!/usr/bin/env python

import numpy as np
import math

"""
Helper functions for use with Latent Semantic Indexing  via
numpy.linalg.svd() products.
"""

def getU_k(u, k):
    return u[:,0:k]

def getS_k(s, k):
    return np.diag(s)[0:k,0:k]

def getV_k(v, k):
    return v[:,0,k]

def getTermConcepts(u, s, k):
    u_k = getU_k(u, k)
    s_k = getS_k(s, k)
    return np.transpose(u_k.dot(np.linalg.inv(s_k)))

def showConcept(u, k, concept, topn=10, reverse=True):
    u_k = getU_k(u, k)
    termValues = u_k[:,concept]
    return sorted([(value, term) for term, value in enumerate(termValues)],
                  key=lambda x: x[0], reverse=reverse)[0:topn]

def conceptCorrelation(u, conceptA, conceptB):
    meanA = sum(u[:,conceptA])/u.shape[0]
    meanB = sum(u[:,conceptB])/u.shape[0]
    numerator = np.dot(u[:,conceptA] - meanA, u[:,conceptB] - meanB)
    varianceA = np.dot(u[:,conceptA] - meanA, u[:,conceptA] - meanA)
    varianceB = np.dot(u[:,conceptB] - meanA, u[:,conceptB] - meanB)
    return numerator/math.sqrt(varianceA*varianceB)

