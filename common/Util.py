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
        sys.exit(-1)
        return None

def getAndCheckFilename(fname):
    if not os.path.isfile(fname):
        print >> sys.stderr, 'error: Cannot find %s' % fname
        sys.exit(-1)
    return fname

def getStopwords(fname):
    if not os.path.isfile(fname):
        print >> sys.stderr, 'error: Stop words file not found: %s' % fname
        sys.exit(-1)
    with open(fname, 'r') as f:
        try:
            stopwords = f.readline().split(',')
        except:
            print >> sys.stderr, 'error: Failed to parse stop words.'
            sys.exit(-1)
    return stopwords
