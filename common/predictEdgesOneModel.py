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
import Util as util
import Prediction_util as pred
from KNNSearchEngine import KNNSearchEngine

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

    model_filename = util.getAndCheckFilename(args[0])
    graph1_filename = util.getAndCheckFilename(args[1])
    graph2_filename = util.getAndCheckFilename(args[2])

    # load model
    print 'Loading model from %s. . .' % model_filename
    data, dictionary = util.loadModel(model_filename)

    # Get popularity
    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph_fname = util.getAndCheckFilename(options.popgraph)
        popgraph = util.loadPickle(popgraph_fname)
        popDictionary = pred.getPopDictionary(popgraph)
    else:
        popDictionary = None

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = util.loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = util.loadPickle(graph2_filename)

    # partition data and dictionary
    print 'Partitioning data and directory. . . '
    data1, dictionary1 = partitionModel(data, dictionary, graph1)
    data2, dictionary2 = partitionModel(data, dictionary, graph2)

    # create search engine
    print 'Creating KNN search engine of graph2 from model. . .'
    searchEngine = KNNSearchEngine(data2, dictionary2)

    print 'Getting nearest neighbors. . .'
    neighbors = pred.getNeighbors(data1, options.k, 
            searchEngine, popDictionary=popDictionary)

    print 'Predicting edges. . .'
    predicted_edges = pred.makeEdges(neighbors, dictionary1)
    
    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
