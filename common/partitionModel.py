#!/usr/bin/env python

"""
Partitions an LSI model based on given graph partitions.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

# local modules
from Util import loadPickle, getAndCheckFilename, loadModel

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--model1', dest='model1filename',
        default='partitionedModel1.npz',
        help='Name of partitioned model1 NPZ file.', metavar='FILE')
    parser.add_option('--model2', dest='model2filename',
        default='partitionedModel2.npz',
        help='Name of partitioned model2 NPZ file.', metavar='FILE')
    parser.add_option('--ident-map', dest='identMap', default=None,
        help='Name of pickled identity matrix.', metavar='FILE')
    return parser

def getIdentityMap(numDim):
    identMap = []
    for i in range(numDim):
        column_vector = []
        for j in range(numDim):
            if j == i:
                column_vector.append(1.0)
            else:
                column_vector.append(0.0)
        identMap.append(column_vector)
    return identMap

def partitionModel(u, s, v, dictionary, graphP):
    uP = None
    vP = None
    dictionaryP = []
    for i in range(len(dictionary)):
        if dictionary[i] in graphP:
            if uP is None:
                uP = u[i,:].reshape([1, u.shape[1]])
                vP = v[:,i].reshape([v.shape[0], 1])
            else:
                uP = np.append(uP, u[i,:].reshape([1, u.shape[1]]), axis=0)
                vP = np.append(vP, v[:,i].reshape([v.shape[0], 1]), axis=1)
            dictionaryP.append(dictionary[i])
    return uP, s, vP, dictionaryP
            
def main():
    # Parse options
    usage = 'Usage: %prog [options] modelfile graph1 graph2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')

    model_filename = getAndCheckFilename(args[0])
    graph1_filename = getAndCheckFilename(args[1])
    graph2_filename = getAndCheckFilename(args[2])

    # load model
    print 'Loading model from %s. . .' % model_filename
    npzfile = np.load(model_filename)
    u = npzfile['u']
    s = npzfile['s']
    v = npzfile['v']
    dictionary = npzfile['dictionary']

    # load graphs
    print 'Loading graph1 from %s. . .' % graph1_filename
    graph1 = loadPickle(graph1_filename)
    print 'Loading graph2 from %s. . .' % graph2_filename
    graph2 = loadPickle(graph2_filename)

    # partition model
    print 'Partitioning model. . .'
    u1, s1, v1, dictionary1 = partitionModel(u, s, v, dictionary, graph1)
    u2, s2, v2, dictionary2 = partitionModel(u, s, v, dictionary, graph2)

    # save partitioned models to disk
    print 'Saving model1 partition to %s. . .' % options.model1filename
    np.savez(options.model1filename, u=u1, s=s1, v=v1, dictionary=dictionary1)
    print 'Saving model2 partition to %s. . .' % options.model2filename
    np.savez(options.model2filename, u=u2, s=s2, v=v2, dictionary=dictionary2)

    # make identity map
    if options.identMap is not None:
        identMap = getIdentityMap(len(s))
        print 'Saving identity map to %s. . .' % options.identMap
        pickle.dump(identMap, open(options.identMap, 'w'))

if __name__ == '__main__':
    main()
