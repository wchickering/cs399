#!/usr/bin/env python
"""
General helper functions
"""

import os
import sys
import pickle
import numpy as np
import LDA_util as lda
import LSI_util as lsi

def loadPickle(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

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

def getAndCheckFilename(fname):
    if not os.path.isfile(fname):
        parser.error('Cannot find %s' % fname)
    return fname

def getStopwords(fname):
    if os.path.isfile(fname):
        with open(fname, 'r') as f:
            try:
                stopwords = f.readline().split(',')
            except:
                print >> sys.stderr, 'Failed to parse stop words.'
                return
    else:
        print >> sys.stderr,\
            'WARNING: stop words file not found: %s' % options.stopwords
        stopwords = None
    return stopwords
