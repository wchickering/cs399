#!/usr/bin/env python

import numpy as np

# local modules
from TFIDF_util import computeCosineSim, computeInnerProd

class TFIDF_SimilarityCache:
    """
    A class for computing and caching item similarities in TF-IDF space.
    """

    def __init__(self, tfidfs, shortCoeff=0.0, bigramsCoeff=0.0,
                 useCosine=False):
        self.tfidfs = tfidfs
        self.shortCoeff = shortCoeff
        self.bigramsCoeff = bigramsCoeff
        self.useCosine = useCosine
        self.computed = False

    def preComputeSims(self, items1, items2):
        self.dictionary1 = self._makeItemDict(items1)
        self.dictionary2 = self._makeItemDict(items2)
        self.sims = np.zeros((len(items1), len(items2)))
        for i in range(len(items1)):
            for j in range(len(items2)):
                if self.useCosine:
                    self.sims[i,j] = computeCosineSim(
                        items1[i], items2[j], self.tfidfs,
                        shortCoeff=self.shortCoeff,
                        bigramsCoeff=self.bigramsCoeff
                    )
                else:
                    self.sims[i,j] = computeInnerProd(
                        items1[i], items2[j], self.tfidfs,
                        shortCoeff=self.shortCoeff,
                        bigramsCoeff=self.bigramsCoeff
                    )
        self.computed = True

    def getSim(self, item1, item2):
        assert(self.computed)
        return self.sims[self.dictionary1[item1], self.dictionary2[item2]]

    def _makeItemDict(self, items):
        dictionary = {}
        for i in range(len(items)):
            dictionary[items[i]] = i
        return dictionary

