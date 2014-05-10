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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
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

def predictEdges(data1, dictionary1, k, searchEngine):
    predicted_edges = []
    for index, node in dictionary1.items():
        distances, neighbors = searchEngine.kneighbors(data1[:, index], k)
        predicted_edges += [(node, int(n)) for n in neighbors[0]]
    return predicted_edges

def partitionModel(data, dictionary, graph_part):
    idx_part = 0
    data_part = []
    dictionary_part = {}
    for idx, node in dictionary.items():
        if node in graph_part:
            data_part.append(data[:,idx_part].transpose())
            dictionary_part[idx_part] = node
            idx_part += 1
    return np.array(data_part).transpose(), dictionary_part

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
    searchEngine = KNNSearchEngine(data2.transpose(), dictionary2)

    print 'Predicting edges. . .'
    predicted_edges = predictEdges(data1, dictionary1, options.k, searchEngine)
    
    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()