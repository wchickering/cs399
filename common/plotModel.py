#!/usr/bin/env python

"""
Produce a variety of plots for the purpose of analyzing a latent variable model.
"""

from optparse import OptionParser
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
import sys

# local modules
import LDA_util as lda
import LSI_util as lsi
from KNNSearchEngine import KNNSearchEngine

# params
saveFormat = 'jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--ldafile', dest='ldafile', default=None,
        help='Pickled LDA model.', metavar='FILE')
    parser.add_option('--svdfile', dest='svdfile', default=None,
        help='NPZ file of SVD products.', metavar='FILE')
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of concepts in LSI model.', metavar='NUM')
    parser.add_option('--graph', dest='graphfile', default=None,
        help='Pickled recommendation graph.', metavar='FILE')
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def plotModelTopics(data, numBins, savedir, xlim=None, show=False):
    first = True
    for topic in range(data.shape[0]):
        if first:
            first = False
        else:
            plt.figure()
        values = data[topic,:]
        n, bins, patches = plt.hist(values, numBins)
        if xlim is not None:
            plt.xlim(xlim)
        plt.savefig(os.path.join(savedir, 'topic%d.%s' % (topic, saveFormat)))
    if show:
        plt.show()

# TODO: Make this efficient
def plotGraphAnalysis(graph, searchEngine, savedir, numBins=100, show=False):
    items = [item for item in searchEngine.dictionary.values() if item in graph]
    graphNeighbors = [graph[item][0] for item in items]
    distances, topicNeighbors =\
        searchEngine.kneighborsByName(items, n_neighbors=numBins)
    neighborRanks = []
    for i in range(len(items)):
        topicNbrs = np.array(topicNeighbors[i])
        graphNbrs = np.array(graphNeighbors[i])[np.newaxis].transpose()
        ranks = np.where(topicNbrs==graphNbrs)[1]
        neighborRanks += ranks.tolist()
        # place all missing ranks in extra overflow bin
        neighborRanks += [numBins]*(graphNbrs.shape[0] - ranks.shape[0])
    plt.figure()
    n, bins, patches = plt.hist(neighborRanks, numBins+1)
    plt.xlim([0,numBins])
    plt.savefig(os.path.join(savedir, 'graphAnalysis.%s' % saveFormat))
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.ldafile is None and options.svdfile is None:
        print >> sys.stderr,\
            'ERROR: Must provide either an LDA model or SVD products.'
        return
    if options.savedir is None:
        savedir = os.getcwd()
    elif os.path.isdir(options.savedir):
        savedir = options.savedir
    else:
        print >> sys.stderr, 'ERROR: Cannot find dir: %s' % options.savedir
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
        data = lda.getTopicGivenItemProbs(ldamodel)
        xlim = [0.0,1.0]
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
        data = lsi.getTermConcepts(u, s, options.k)
        xlim = None

    # build search engine
    searchEngine = KNNSearchEngine(data.transpose(), dictionary)

    # generate plots
    print 'Plotting topic distributions. . .'
    #plotModelTopics(data, options.bins, savedir, xlim=xlim, show=options.show)

    # analyze relation to original graph
    if options.graphfile is not None:
        if not os.path.isfile(options.graphfile):
            print >> sys.stdeerr, 'WARNING: Cannot find %s' % options.graphfile
        else:
            print 'Loading graph from %s. . .' % options.graphfile
            graph = loadGraph(options.graphfile)
            print 'Plotting graph analysis. . .'
            plotGraphAnalysis(graph, searchEngine, savedir,
                              numBins=options.bins, show=options.show)

if __name__ == '__main__':
    main()
