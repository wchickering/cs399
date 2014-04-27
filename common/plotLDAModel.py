#!/usr/bin/env python

from optparse import OptionParser
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
import sys

import LDA_util as lda

# params
saveFormat = 'jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def plotModel(model, numBins, savedir, show=False):
    p_topic_given_item = lda.getTopicGivenItemProbs(model)
    first = True
    for topic in range(model.num_topics):
        if first:
            first = False
        else:
            plt.figure()
        probs = p_topic_given_item[topic,:]
        n, bins, patches = plt.hist(probs, numBins)
        plt.xlim([0.0,1.0])
        plt.savefig(os.path.join(savedir, 'topic%d.%s' % (topic, saveFormat)))
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options] <model.pickle>'
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

    # load lda model
    print 'Loading model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # generate plots
    print 'Plotting topic distributions. . .'
    plotModel(model, options.bins, savedir, options.show)

if __name__ == '__main__':
    main()
