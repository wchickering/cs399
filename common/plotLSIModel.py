#!/usr/bin/env python

from optparse import OptionParser
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
import sys

import LSI_util as lsi

# params
saveFormat = 'jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of concepts in LSI model.', metavar='NUM')
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def plotModel(u, s, k, numBins, savedir, show=False):
    term_concepts = lsi.getTermConcepts(u, s, k)
    first = True
    for concept in range(k):
        if first:
            first = False
        else:
            plt.figure()
        values = term_concepts[concept,:]
        n, bins, patches = plt.hist(values, numBins)
        plt.savefig(os.path.join(savedir,
                                 'concept%d.%s' % (concept, saveFormat)))
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options] <svd.npz>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % modelfname
        return
    if options.savedir is None:
        savedir = os.getcwd()
    elif os.path.isdir(options.savedir):
        savedir = options.savedir
    else:
        print >> sys.stderr, 'ERROR: Cannot find dir: %s' % options.savedir
        return

    # load LSI model
    print 'Loading model. . .'
    npzfile = np.load(modelfname)
    u = npzfile['u']
    s = npzfile['s']
    v = npzfile['v']
    dictionary = npzfile['dictionary']

    # generate plots
    print 'Plotting concept distributions. . .'
    plotModel(u, s, options.k, options.bins, savedir, options.show)

if __name__ == '__main__':
    main()
