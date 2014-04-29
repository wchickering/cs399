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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--ldafile', dest='ldafile', default=None,
        help='Pickled LDA model.', metavar='FILE')
    parser.add_option('--svdfile', dest='svdfile', default=None,
        help='NPZ file of SVD products.', metavar='FILE')
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of concepts in LSI model.', metavar='NUM')
    parser.add_option('-n', '--numedges', type='int', dest='numedges',
        default=4, help='Number of outgoing edges per node.', metavar='NUM')
    parser.add_option('-o', '--output', dest='outfilename',
        default='graphFromLDA.pickle',
        help='Output pickle file containing recommendation graph.',
        metavar='FILE')
    return parser

def makeGraph(neighbors):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    for nodes in neighbors:
        source = int(nodes[0])
        if source not in graph:
            node_cnt += 1
            graph[source] = ([],[])
        for i in range(1, len(nodes)):
            dest = int(nodes[i])
            graph[source][0].append(dest)
            if dest not in graph:
                node_cnt += 1
                graph[dest] = ([],[])
            graph[dest][1].append(source)
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
        data = lsi.getTermConcepts(u, s, options.k).transpose()

    # build search engine
    searchEngine = KNNSearchEngine(data, dictionary)

    # find neighbors
    distances, neighbors =\
        searchEngine.kneighbors(data, n_neighbors=options.numedges+1)

    # make graph
    graph = makeGraph(neighbors)

    # save graph
    pickle.dump(graph, open(options.outfilename, 'w'))

if __name__ == '__main__':
    main()

