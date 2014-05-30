#!/usr/bin/env python

"""
Prints an LDA model's topic mixture for a particular item.
"""

from optparse import OptionParser
import pickle
import os
import sys

import LDA_util as lda

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] lda.pickle itemId'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return
    item = args[1]

    # load lda model
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # print item's topic mixture
    p_topic_given_item = lda.getTopicGivenItemProbs(model)
    mixture = p_topic_given_item[:,model.id2word.token2id[item]]
    for topic in range(model.num_topics):
        print '%d: %0.3f' % (topic, mixture[topic])

if __name__ == '__main__':
    main()
