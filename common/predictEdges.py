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
from Util import loadPickle, getAndCheckFilename, loadModel
from Prediction_util import getNeighbors, makeEdges, getPopDictionary
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

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicMap.pickle modelfile1 modelfile2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 

    topic_map_filename = getAndCheckFilename(args[0])
    model1_filename = getAndCheckFilename(args[1])
    model2_filename = getAndCheckFilename(args[2])

    # Get popularity
    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph_fname = getAndCheckFilename(options.popgraph)
        popgraph = loadPickle(popgraph_fname)
        popDictionary = getPopDictionary(popgraph)
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
    transformed_data1 = np.dot(data1, np.array(topic_map).transpose())

    # create search engine
    print 'Creating KNN search engine from model2. . .'
    searchEngine = KNNSearchEngine(data2, dictionary2)

    print 'Getting nearest neighbors. . .'
    neighbors = getNeighbors(transformed_data1, 
            options.k, searchEngine, popDictionary=popDictionary)

    print 'Predicting edges. . .'
    predicted_edges = makeEdges(neighbors, dictionary1)

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
