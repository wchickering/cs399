#!/usr/bin/env python

"""
Helper functions for working with sparse TF-IDF vectors.
"""

import math

def _getCosineSimFactors(vector1, vector2):
    innerProd = 0.0
    normSqr1 = 0.0
    for key1, value1 in vector1.items():
        normSqr1 += value1**2
        if key1 in vector2:
            innerProd += value1*vector2[key1]
    normSqr2 = 0.0
    for key2, value2 in vector2.items():
        normSqr2 += value2**2
    return innerProd, normSqr1, normSqr2

def computeCosineSim(item1, item2, tfidfs, shortCoeff=0.0, bigramsCoeff=0.0):
    innerProd, normSqr1, normSqr2 = _getCosineSimFactors(tfidfs['terms'][item1],
                                                         tfidfs['terms'][item2])
    if shortCoeff > 0.0:
        ip, ns1, ns2 = _getCosineSimFactors(tfidfs['short'][item1],
                                            tfidfs['short'][item2])
        innerProd += shortCoeff*ip
        normSqr1 += shortCoeff*ns1
        normSqr2 += shortCoeff*ns2
    if bigramsCoeff > 0.0:
        ip, ns1, ns2 = _getCosineSimFactors(tfidfs['bigrams'][item1],
                                            tfidfs['bigrams'][item2])
        innerProd += bigramsCoeff*ip
        normSqr1 += bigramsCoeff*ns1
        normSqr2 += bigramsCoeff*ns2
    return innerProd/math.sqrt(normSqr1*normSqr2)

def _getInnerProd(vector1, vector2):
    return sum(
        [vector1[key1]*vector2[key1] for key1 in vector1 if key1 in vector2]
    )

def computeInnerProd(item1, item2, tfidfs, shortCoeff=0.0, bigramsCoeff=0.0):
    innerProd = _getInnerProd(tfidfs['terms'][item1], tfidfs['terms'][item2])
    if shortCoeff > 0.0:
        innerProd += shortCoeff*_getInnerProd(tfidfs['short'][item1],
                                              tfidfs['short'][item2])
    if bigramsCoeff > 0.0:
        innerProd += bigramsCoeff*_getInnerProd(tfidfs['bigrams'][item1],
                                                tfidfs['bigrams'][item2])
    return innerProd
