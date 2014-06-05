#!/usr/bin/env python

"""
Partitions an LSI model based on given graph partitions.
"""

from optparse import OptionParser
import os
import sys
import numpy as np

# local modules
from Util import loadPickle, getAndCheckFilename

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--model1', dest='modelFilename1',
        default='partitionedModel1.npz',
        help='Name of partitioned model1 NPZ file.', metavar='FILE')
    parser.add_option('--model2', dest='modelFilename2',
        default='partitionedModel2.npz',
        help='Name of partitioned model2 NPZ file.', metavar='FILE')
    return parser

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

    modelFilename = getAndCheckFilename(args[0])
    graphFilename1 = getAndCheckFilename(args[1])
    graphFilename2 = getAndCheckFilename(args[2])

    # load model
    print 'Loading model from %s. . .' % modelFilename
    npzfile = np.load(modelFilename)
    u = npzfile['u']
    s = npzfile['s']
    v = npzfile['v']
    dictionary = npzfile['dictionary']

    # load graphs
    print 'Loading graph1 from %s. . .' % graphFilename1
    graph1 = loadPickle(graphFilename1)
    print 'Loading graph2 from %s. . .' % graphFilename2
    graph2 = loadPickle(graphFilename2)

    # partition model
    print 'Partitioning model. . .'
    u1, s1, v1, dictionary1 = partitionModel(u, s, v, dictionary, graph1)
    u2, s2, v2, dictionary2 = partitionModel(u, s, v, dictionary, graph2)

    # save partitioned models to disk
    print 'Saving model1 partition to %s. . .' % options.modelFilename1
    np.savez(options.modelFilename1, u=u1, s=s1, v=v1, dictionary=dictionary1)
    print 'Saving model2 partition to %s. . .' % options.modelFilename2
    np.savez(options.modelFilename2, u=u2, s=s2, v=v2, dictionary=dictionary2)

if __name__ == '__main__':
    main()
