#!/usr/bin/env python

"""
Predicts the edges across two LDA/LSI models.
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
        data = lda.getTopicGivenItemProbs(model).transpose()
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
        data = lsi.getTermConcepts(u, s).transpose()
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

def partitionModel(data, dictionary, graph_part):
    idx_part = 0
    data_part = None
    dictionary_part = {}
    for idx, node in dictionary.items():
        if node in graph_part:
            if data_part is None:
                data_part = data[idx,:].reshape([1, data.shape[1]])
            else:
                numRows = data_part.shape[0] + 1
                numCols = data_part.shape[1]
                data_part = np.append(data_part, data[idx,:])\
                            .reshape([numRows, numCols])
            dictionary_part[idx_part] = node
            idx_part += 1
    return data_part, dictionary_part

def main():
    # Parse options
    usage = 'Usage: %prog [options] modelfile graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 
    model_filename = args[0]
    if not os.path.isfile(model_filename):
        parser.error('Cannot find %s' % model_filename)
    graph1_filename = args[1]
    if not os.path.isfile(graph1_filename):
        parser.error('Cannot find %s' % graph1_filename)
    graph2_filename = args[2]
    if not os.path.isfile(graph2_filename):
        parser.error('Cannot find %s' % graph2_filename)

    # load model
    print 'Loading model from %s. . .' % model_filename
    data, dictionary = loadModel(model_filename)

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

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)

    # partition data and dictionary
    print 'Partitioning data and directory. . . '
    data1, dictionary1 = partitionModel(data, dictionary, graph1)
    data2, dictionary2 = partitionModel(data, dictionary, graph2)

    # create search engine
    print 'Creating KNN search engine of graph2 from model. . .'
    searchEngine = KNNSearchEngine(data2, dictionary2)

    print 'Getting nearest neighbors. . .'
    neighbors = getNeighbors(data1, options.k, searchEngine,
                             popDictionary=popDictionary)

    print 'Predicting edges. . .'
    predicted_edges = predictEdges(neighbors, dictionary1)
    
    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
