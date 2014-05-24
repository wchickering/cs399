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
        model = loadPickle(filename)
        return lda.loadLDAModel(model)
    elif filename.endswith('.npz'):
        npzfile = np.load(filename)
        return lsi.loadLSIModel(npzfile)
    else:
        print >> sys.stderr,\
            'error: Model file must be either a .pickle or .npz file.'
        return None

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
