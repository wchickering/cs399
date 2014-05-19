#!/usr/bin/env python

"""
Predicts the edges across two LDA/LSI model.
"""
from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

# local modules
import LDA_util as lda
import LSI_util as lsi
from KNNSearchEngine import KNNSearchEngine

# params
topn = 100
basePop = 0.1
alpha = 1.0

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--popgraph', dest='popgraph', default=None,
        help='Picked graph representing item "popularity".', metavar='FILE')
    return parser

def loadPickle(fname):
    with open(fname, 'r') as f:
        obj = pickle.load(f)
    return obj

def loadModel(filename):
    if filename.endswith('.pickle'):
        # load LDA model
        model = loadPickle(filename)
        dictionary = {}
        for i, node in model.id2word.items():
            dictionary[i] = int(node)
        data = lda.getTopicGivenItemProbs(model)
    elif filename.endswith('.npz'):
        # load LSI model
        npzfile = np.load(filename)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        nodes = npzfile['dictionary']
        dictionary = {}
        for i in range(len(nodes)):
            dictionary[i] = int(nodes[i])
        data = lsi.getTermConcepts(u, s)
    else:
        print >> sys.stderr,\
            'error: Model file must be either a .pickle or .npz file.'
        return None
    return data, dictionary

def getNeighbors(data, k, searchEngine, popDictionary):
    if popDictionary is None:
        distances, neighbors =\
            searchEngine.kneighbors(data, n_neighbors=k)
    else:
        distances, neighbors =\
            searchEngine.kneighborsWeighted(data, popDictionary,
                  topn, alpha, basePop, n_neighbors=k)
    return neighbors


def predictEdges(neighbors, dictionary):
    predicted_edges = []
    for index, node in dictionary.items():
        predicted_edges += [(node, int(n)) for n in neighbors[index]]
    return predicted_edges

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicMap.pickle modelfile1 modelfile2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    topic_map_filename = args[0]
    if not os.path.isfile(topic_map_filename):
        parser.error('Cannot find %s' % topic_map_filename)
    model1_filename = args[1]
    if not os.path.isfile(model1_filename):
        parser.error('Cannot find %s' % model1_filename)
    model2_filename = args[2]
    if not os.path.isfile(model2_filename):
        parser.error('Cannot find %s' % model2_filename)

    # Get popularity
    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph = loadPickle(options.popgraph)
        popDictionary = {}
        for item in popgraph:
            # set popularity equal to in-degree
            popDictionary[item] = len(popgraph[item][1])
    else:
        popDictionary = None

    # load topic map
    print 'Loading topic map from %s. . .' % topic_map_filename
    topic_map = loadPickle(topic_map_filename)

    # load models
    print 'Loading model1 from %s. . .' % model1_filename
    data1, dictionary1 = loadModel(model1_filename)
    print 'Loading model2 from %s. . .' % model2_filename
    data2, dictionary2 = loadModel(model2_filename)

    # transform to common topic space
    print 'Transforming topic space 1 to topic space 2. . .'
    transformed_data1 = np.dot(topic_map, data1)

    # create search engine
    print 'Creating KNN search engine from model2. . .'
    searchEngine = KNNSearchEngine(data2.transpose(), dictionary2)

    print 'Getting nearest neighbors. . .'
    neighbors = getNeighbors(transformed_data1.transpose(), options.k,
                             searchEngine, popDictionary=popDictionary)

    print 'Predicting edges. . .'
    predicted_edges = predictEdges(neighbors, dictionary1)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
