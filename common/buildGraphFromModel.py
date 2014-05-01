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
import LDA_util as lda
import LSI_util as lsi
from KNNSearchEngine import KNNSearchEngine

# params
topn = 100

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--ldafile', dest='ldafile', default=None,
        help='Pickled LDA model.', metavar='FILE')
    parser.add_option('--svdfile', dest='svdfile', default=None,
        help='NPZ file of SVD products.', metavar='FILE')
    parser.add_option('--popmatrix', dest='popmatrix', default=None,
        help='NPZ file of "popularity" random walk.', metavar='FILE')
    parser.add_option('-n', '--numedges', type='int', dest='numedges',
        default=4, help='Number of outgoing edges per node.', metavar='NUM')
    parser.add_option('-o', '--output', dest='outfilename',
        default='graphFromLDA.pickle',
        help='Output pickle file containing recommendation graph.',
        metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

# TODO: Clean up this function!
def getNeighbors(data, dictionary, numEdges, searchEngine, popDictionary=None):
    if popDictionary is None:
        distances, neighbors =\
            searchEngine.kneighbors(data, n_neighbors=numEdges+1)
    else:
        distances, origNeighbors =\
            searchEngine.kneighbors(data, n_neighbors=topn)

        # weight distances by "popularity"
        newDistances = np.zeros(distances.shape)
        for i in range(distances.shape[0]):
            for j in range(distances.shape[1]):
                newDistances[i][j] =\
                    distances[i][j]/popDictionary[origNeighbors[i][j]]

        # re-sort neighbors by weighted distance
        neighborDistances = np.dstack((newDistances, origNeighbors))
        h, w = neighborDistances.shape[0], neighborDistances.shape[1]
        mappedNeighborDistances = map(tuple, neighborDistances\
                                             .reshape((h*w, 2)))
        structMappedNeighborDistances =\
            np.array(mappedNeighborDistances,
                     dtype={'names':['distance', 'neighbor'],\
                            'formats':['f4', 'i4']}).reshape((h, w))
        sortedNeighborDistances = np.sort(structMappedNeighborDistances, axis=1,
                                          order='distance')
        neighbors = sortedNeighborDistances['neighbor'][:,0:numEdges+1]

    # Preclude self-loops
    filteredNeighbors = []
    for i in range(len(neighbors)):
        filtNbrs = [n for n in neighbors[i] if n != dictionary[i]]
        filteredNeighbors.append(filtNbrs[0:numEdges])

    return np.array(filteredNeighbors)

def makeGraph(dictionary, neighbors):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    for index, source in dictionary.items():
        if source not in graph:
            node_cnt += 1
            graph[source] = ([],[])
        for neighbor in neighbors[index]:
            graph[source][0].append(neighbor)
            if neighbor not in graph:
                node_cnt += 1
                graph[neighbor] = ([],[])
            graph[neighbor][1].append(source)
            edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.ldafile is None and options.svdfile is None:
        print >> sys.stderr,\
            'ERROR: Must provide either an LDA model or SVD products.'
        return

    # load model
    if options.ldafile is not None:
        # process LDA model
        if not os.path.isfile(options.ldafile):
            print >> sys.stderr, 'ERROR: Cannot find %s' % options.ldafile
            return
        print >> sys.stderr, 'Load LDA model. . .'
        with open(options.ldafile, 'r') as f:
            ldamodel = pickle.load(f)
        dictionary = {}
        for i, item in ldamodel.id2word.items():
            dictionary[i] = int(item)
        data = lda.getTopicGivenItemProbs(ldamodel).transpose()
    else:
        # process LSI model
        if not os.path.isfile(options.svdfile):
            print >> sys.stderr, 'ERROR: Cannot finf %s' % options.svdfile
            return
        print >> sys.stderr, 'Load LSI model. . .'
        npzfile = np.load(options.svdfile)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        items = npzfile['dictionary']
        dictionary = {}
        for i in range(len(items)):
            dictionary[i] = int(items[i])
        data = lsi.getTermConcepts(u, s).transpose()

    if options.popmatrix:
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
    searchEngine = KNNSearchEngine(data, dictionary)

    # find neighbors
    neighbors = getNeighbors(data, dictionary, options.numedges, searchEngine,
                             popDictionary=popDictionary)

    # make graph
    graph = makeGraph(dictionary, neighbors)

    # save graph
    pickle.dump(graph, open(options.outfilename, 'w'))

if __name__ == '__main__':
    main()

