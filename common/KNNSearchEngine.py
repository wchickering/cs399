#!/usr/bin/env python

from sklearn.neighbors import NearestNeighbors
import numpy as np

class KNNSearchEngine:
    """
    k nearest neighbor search engine. Essentially a wrapper of
    sklearn.neighbors.NearestNeighbors class.
    """

    def __init__(self, data, dictionary, algorithm='ball_tree', leaf_size=30):
        self.dictionary = dictionary
        self._makeReverseDictionary()
        self.data = data
        self.nbrs = NearestNeighbors(algorithm=algorithm, leaf_size=leaf_size)
        self.nbrs.fit(data)

    def kneighbors(self, query, n_neighbors=10):
        distances, indexes =\
            self.nbrs.kneighbors(query, n_neighbors=n_neighbors)
        neighbors = [[self.dictionary[i] for i in index] for index in indexes]
        return distances, neighbors

    def kneighborsByName(self, items, n_neighbors=10):
        query = [self.data[self.reverseDictionary[item]] for item in items]
        return self.kneighbors(query, n_neighbors=n_neighbors)

    def _makeReverseDictionary(self):
        self.reverseDictionary = {}
        for i in range(len(self.dictionary)):
            self.reverseDictionary[self.dictionary[i]] = i


##########################
# ROUGH UNIT TEST
##########################

import LDA_util as lda
import pickle

from SessionTranslator import SessionTranslator

# params
modelfname = 'data/lda_randomWalk_Dresses_0.1_40.pickle'
dbname = 'data/macys.db'

def main():
    # load lda model
    print 'Load LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get translator
    translator = SessionTranslator(dbname)

    data = lda.getTopicGivenItemProbs(model).transpose()
    dictionary = model.id2word
    searchEngine = KNNSearchEngine(data, dictionary)
    index = 0
    item = dictionary[index]
    description = translator.sessionToDesc([item])

    print 'Finding neighbors of: (%s) %s' % (item, description)
    query = [data[index]]
    distances, neighbors = searchEngine.kneighbors(query)
    neighbor_descs = translator.sessionToDesc(neighbors[0])
    print 'Neighbors:'
    for i in range(len(neighbor_descs)):
        print '(%s) %s (dist: %f)' %\
              (neighbors[0][i], neighbor_descs[i], distances[0][i])

    print ''
    print 'Finding same neighbors by name. . .'
    items = [item]
    distances, neighbors = searchEngine.kneighborsByName(items)
    neighbor_descs = translator.sessionToDesc(neighbors[0])
    print 'Neighbors:'
    for i in range(len(neighbor_descs)):
        print '(%s) %s (dist: %f)' %\
              (neighbors[0][i], neighbor_descs[i], distances[0][i])

if __name__ == '__main__':
    main()
