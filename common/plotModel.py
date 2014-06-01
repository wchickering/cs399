#!/usr/bin/env python

"""
Produce a variety of plots for the purpose of analyzing a latent variable model.
"""

from optparse import OptionParser
import matplotlib.pyplot as plt
import numpy as np
import math
import pickle
import os
import sys

# local modules
from Graph_util import loadGraph
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
    parser.add_option('--graph', dest='graphfile', default=None,
        help='Pickled recommendation graph.', metavar='FILE')
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--3sigma', action='store_true', dest='threeSigma',
        default=False, help='For LSI, use 3 sigma for domain of topic plots.')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    parser.add_option('--notopicplots', action='store_true',
        dest='notopicplots', default=False, help='Do not produce topic plots.')
    parser.add_option('--pop-vs-norm', action='store_true', dest='popVsNorm',
        default=False, help='Plot Popularity vs L2 Norm.')
    return parser

def plotModelTopics(data, numBins, savedir, xlim=None, show=False):
    first = True
    for topic in range(data.shape[0]):
        if first:
            first = False
        else:
            plt.figure()
        values = data[topic,:]
        n, bins, patches = plt.hist(values, bins=numBins, range=xlim)
        plt.title('Topic %d Distribution' % topic)
        plt.ylabel('Number of Items (out of %d)' % data.shape[1])
        plt.xlabel('Topic Amount')
        if xlim is not None:
            plt.xlim(xlim)
        if savedir is not None:
            plt.savefig(os.path.join(savedir,
                                     'topic%d.%s' % (topic, saveFormat)))
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
        #neighborRanks += [numBins]*(graphNbrs.shape[0] - ranks.shape[0])
    plt.figure()
    n, bins, patches = plt.hist(neighborRanks, numBins, normed=1)
    plt.title('Rank of graph NN measured in topic space')
    plt.ylabel('Fraction of Edges')
    plt.xlabel('NN Rank in Topic Space')
    plt.xlim([0,numBins])
    if savedir is not None:
        plt.savefig(os.path.join(savedir, 'graphAnalysis.%s' % saveFormat))
    if show:
        plt.show()

def plotPopVsNorm(graph, data, dictionary, savedir=None, show=False):
    pop = []
    norm = []
    for i in range(data.shape[1]):
        item = dictionary[i]
        pop.append(len(graph[item][1]))
        norm.append(np.linalg.norm(data[:,i]))
    plt.hist2d(pop, norm, bins=100, range=[[0, 20], [0.0, 0.2]])
    plt.title('Popularity vs Norm')
    plt.xlabel('Node In-degree')
    plt.ylabel('Item L2 Norm')
    if savedir is not None:
        plt.savefig(os.path.join(savedir, 'popVsNorm.%s' % saveFormat))
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.ldafile is None and options.svdfile is None:
        parser.error('Must provide either an LDA model or SVD products.')
    if options.savedir is None:
        savedir = None
    elif os.path.isdir(options.savedir):
        savedir = options.savedir
    else:
        if os.path.isdir(os.path.split(options.savedir)[0]):
            print 'Creating directory %s. . .' % options.savedir
            os.mkdir(options.savedir)
            savedir = options.savedir
        else:
            parser.error('Cannot find dir: %s' % options.savedir)

    # load model
    if options.ldafile is not None:
        # process LDA model
        if not os.path.isfile(options.ldafile):
            parser.error('Cannot find %s' % options.ldafile)
        print >> sys.stderr, 'Loading LDA model from %s. . .' % options.ldafile
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
            parser.error('Cannot find %s' % options.svdfile)
        print >> sys.stderr, 'Loading LSI model from %s. . .' % options.svdfile
        npzfile = np.load(options.svdfile)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        items = npzfile['dictionary']
        dictionary = {}
        for i in range(len(items)):
            dictionary[i] = int(items[i])
        data = lsi.getTermConcepts(u, s)
        xlim = None
        print 'Singular Values =', s

    if options.show or savedir is not None:
        # build search engine
        searchEngine = KNNSearchEngine(data.transpose(), dictionary)

        # generate plots
        if not options.notopicplots:
            if options.threeSigma:
                xmax = 3*math.sqrt(1.0/data.shape[1])
                xlim = (-xmax, xmax)
            print 'Plotting topic distributions. . .'
            plotModelTopics(data, options.bins, savedir, xlim=xlim,
                            show=options.show)

        # analyze relation to original graph
        if options.graphfile is not None:
            if not os.path.isfile(options.graphfile):
                print >> sys.stdeerr,\
                    'warning: Cannot find %s' % options.graphfile
            else:
                print 'Loading graph from %s. . .' % options.graphfile
                graph = loadGraph(options.graphfile)
                if options.popVsNorm:
                    print 'Plotting popularity vs norm. . .'
                    plotPopVsNorm(graph, data, dictionary, savedir=savedir,
                                  show=options.show)
                print 'Plotting graph analysis. . .'
                plotGraphAnalysis(graph, searchEngine, savedir,
                                  numBins=options.bins, show=options.show)

if __name__ == '__main__':
    main()
