#!/usr/bin/env python

"""
Display the topic mixture within a model associated with one or more itemIds.
"""

from optparse import OptionParser
import numpy as np
import pickle
import os
import sys

# local modules
import LDA_util as lda
import LSI_util as lsi

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def loadModel(filename):
    if filename.endswith('.pickle'):
        # load LDA model
        with open(filename, 'r') as f:
            model = pickle.load(f)
        dictionary = {}
        for i, node in model.id2word.items():
            dictionary[int(node)] = i
        matrix = lda.getTopicGivenItemProbs(model)
    elif filename.endswith('.npz'):
        # load LSI model
        npzfile = np.load(filename)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        nodes = npzfile['dictionary']
        dictionary = {}
        for i in range(len(nodes)):
            dictionary[int(nodes[i])] = i
        matrix = lsi.getTermConcepts(u, s)
    else:
        print >> sys.stderr,\
            'error: Model file must be either a .pickle or .npz file.'
        return None
    return matrix, dictionary

def main():
    # Parse options
    usage = 'Usage: %prog [options] modelfile itemId [itemId] [...]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('Wrong number of arguments')
    model_filename = args[0]
    if not os.path.isfile(model_filename):
        parser.error('Cannot find %s' % model_filename)

    # load model
    print 'Loading model from %s. . .' % model_filename
    matrix, dictionary = loadModel(model_filename)

    # display topic mixture(s)
    for itemId in args[1:]:
        print matrix[:,dictionary[int(itemId)]]

if __name__ == '__main__':
    main()
