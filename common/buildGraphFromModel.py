#!/usr/bin/env python

"""
Constructs a directed recommendation graph from an LDA or LSI model.
"""

from optparse import OptionParser
import numpy as np
import pickle
import os
import sys

# local modules
from Graph_util import loadGraph, saveGraph
import LDA_util as lda
import LSI_util as lsi
from KNNSearchEngine import KNNSearchEngine
from Prediction_util import getPopDictionary

# params
topn = 100

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--ldafile', dest='ldafile', default=None,
        help='Pickled LDA model.', metavar='FILE')
    parser.add_option('--svdfile', dest='svdfile', default=None,
        help='NPZ file of SVD products.', metavar='FILE')
    parser.add_option('--walkfile', dest='walkfile', default=None,
        help='NPZ file of Random Walk matrix.', metavar='FILE')
    parser.add_option('--random', action='store_true', dest='random',
        default=False, help='Replace data with random values.')
    parser.add_option('-n', '--numedges', type='int', dest='numedges',
        default=4, help='Number of outgoing edges per node.', metavar='NUM')
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Create a directed graph.')
    parser.add_option('--popmatrix', dest='popmatrix', default=None,
        help='NPZ file of "popularity" random walk.', metavar='FILE')
    parser.add_option('--popgraph', dest='popgraph', default=None,
        help='Picked graph representing item "popularity".', metavar='FILE')
    parser.add_option('--amplify', type='float', dest='amplify', default=1.0,
        help='Scalar by which to multiply latent space query points.',
        metavar='FLOAT')
    parser.add_option('--savefile', dest='savefile',
        default='graphFromModel.pickle',
        help='Save file for re-constructed graph.', metavar='FILE')
    return parser

def makeGraph(dictionary, neighbors, directed=False):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    for index, source in dictionary.items():
        if source not in graph:
            node_cnt += 1
            graph[source] = ([],[])
        for neighbor in neighbors[index]:
            if neighbor not in graph[source][0]:
                graph[source][0].append(neighbor)
            if not directed and neighbor not in graph[source][1]:
                graph[source][1].append(neighbor)
            if neighbor not in graph:
                node_cnt += 1
                graph[neighbor] = ([],[])
            if source not in graph[neighbor][1]:
                graph[neighbor][1].append(source)
            if not directed and source not in graph[neighbor][0]:
                graph[neighbor][0].append(source)
            edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # load model
    if options.ldafile is not None:
        # process LDA model
        if not os.path.isfile(options.ldafile):
            parser.error('Cannot find %s' % options.ldafile)
        print 'Loading LDA model from %s. . .' % options.ldafile
        with open(options.ldafile, 'r') as f:
            ldamodel = pickle.load(f)
        dictionary = {}
        for i, item in ldamodel.id2word.items():
            dictionary[i] = int(item)
        data = lda.getTopicGivenItemProbs(ldamodel).transpose()
    elif options.svdfile is not None:
        # process LSI model
        if not os.path.isfile(options.svdfile):
            parser.error('Cannot find %s' % options.svdfile)
        print 'Loading LSI model from %s. . .' % options.svdfile
        npzfile = np.load(options.svdfile)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        items = npzfile['dictionary']
        dictionary = {}
        for i in range(len(items)):
            dictionary[i] = int(items[i])
        data = lsi.getTermConcepts(u, s).transpose()
    elif options.walkfile is not None:
        # process random walk matrix
        if not os.path.isfile(options.walkfile):
            parser.error('Cannot find %s' % options.walkfile)
        print 'Loading walk matrix from %s. . .' % options.walkfile
        npzfile = np.load(options.walkfile)
        data = npzfile['matrix']
        d = npzfile['dictionary']
        dictionary = {}
        for i in range(len(d)):
            dictionary[i] = int(d[i])
    else:
        parser.error('Must provide LDA model, SVD products, or Walk matrix.')

    if options.random:
        # generate random data
        print 'Generating random data. . .'
        data = np.random.rand(data.shape[0], data.shape[1])

    if options.popgraph:
        print 'Loading "popularity" graph from %s. . .' % options.popgraph
        popgraph = loadGraph(options.popgraph)
        popDictionary = getPopDictionary(popgraph)
    elif options.popmatrix:
        print 'Loading "popularity" matrix from %s. . .' % options.popmatrix
        npzfile = np.load(options.popmatrix)
        m = npzfile['matrix']
        d = npzfile['dictionary']
        popDictionary = {}
        for i in range(m.shape[1]):
            popDictionary[d[i]] = m[0][i]
    else:
        popDictionary = None

    # build search engine
    print 'Building Search Engine. . .'
    searchEngine = KNNSearchEngine(data, dictionary)

    # find neighbors
    print 'Determining neighbors. . .'
    distances, raw_neighbors = searchEngine.kneighbors(
        options.amplify*data,
        options.numedges,
        weights=popDictionary
    )

    # Preclude self-loops
    filteredNeighbors = []
    for i in range(len(raw_neighbors)):
        filtNbrs = [n for n in raw_neighbors[i] if n != dictionary[i]]
        filteredNeighbors.append(filtNbrs[0:options.numedges])

    neighbors =  np.array(filteredNeighbors)

    # make graph
    print 'Constructing graph. . .'
    graph = makeGraph(dictionary, neighbors, options.directed)

    # save graph
    print 'Saving graph to %s. . .' % options.savefile
    saveGraph(graph, options.savefile)

if __name__ == '__main__':
    main()

